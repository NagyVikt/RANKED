import json
import os
import requests
from urllib.parse import urljoin
import logging
import argparse
from datetime import datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from config.config import api_key

# ---------------------- Configuration and Setup ----------------------

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("product_scraper.log"),
        logging.StreamHandler()
    ]
)

# Load environment variables from a .env file
load_dotenv()

# Fetch Scraper API key from environment variables or set it directly
SCRAPER_API_KEY = api_key

if not SCRAPER_API_KEY:
    logging.error("Scraper API key is not set. Please set SCRAPER_API_KEY in your .env file or in the script.")
    exit(1)

# Headers for the HTTP requests
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
}

# ---------------------- Argument Parsing ----------------------

def parse_arguments():
    parser = argparse.ArgumentParser(description='Scrape products from svx.sk and save to a JSON file.')
    parser.add_argument('--category_slug', type=str, required=True, help='Slug of the category to scrape.')
    parser.add_argument('--categories', type=str, default='filtered_categories.json', help='Path to the categories JSON file.')
    parser.add_argument('--output', type=str, default='products.json', help='Filename for the output JSON file.')
    return parser.parse_args()

# ---------------------- Functions ----------------------

def fetch_page(url, api_key, wait_for_selector=None):
    try:
        payload = {
            'api_key': api_key,
            'url': url,
            'render': 'true',
            'device_type': 'desktop'
        }
        if wait_for_selector:
            payload['wait_for_selector'] = wait_for_selector

        response = requests.get('http://api.scraperapi.com/', params=payload, headers=headers)
        response.raise_for_status()
        logging.info(f"Successfully fetched {url}")
        return response.text
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching {url}: {e}")
        raise

def get_total_pages(soup):
    """
    Retrieves the total number of pages in the pagination.

    Args:
        soup (BeautifulSoup): Parsed HTML content of the page.

    Returns:
        int: Total number of pages.
    """
    try:
        # Find the pagination container
        pagination_container = soup.find('div', {'data-html-to-replace': 'pagination'})
        if not pagination_container:
            return 1

        # Find the unordered list within the pagination container
        paginator = pagination_container.find('ul', {'data-testid': 'paginator'})
        if not paginator:
            return 1

        # Find all list items within the paginator
        page_items = paginator.find_all('li')

        page_numbers = []

        for item in page_items:
            # Check for page links
            link = item.find('a')
            if link and link.get_text(strip=True).isdigit():
                page_numbers.append(int(link.get_text(strip=True)))
            else:
                # Check for current page number
                span = item.find('span')
                if span and span.get_text(strip=True).isdigit():
                    page_numbers.append(int(span.get_text(strip=True)))

        if page_numbers:
            total_pages = max(page_numbers)
        else:
            total_pages = 1

        return total_pages
    except Exception as e:
        logging.error(f"Error parsing pagination: {e}")
        return 1


def extract_products(soup):
    products = []
    # Find all product card wrappers
    product_wrappers = soup.find_all('div', {'class': 'product-card-wrapper'})

    for wrapper in product_wrappers:
        try:
            card = wrapper.find('div', {'class': 'product-card'})
            if not card:
                continue

            # Find the product name and URL
            name_tag = card.find('div', {'class': 'inline-flex md:mr-8'}).find('a')
            if not name_tag:
                continue

            name = name_tag.get_text(strip=True)
            product_url = name_tag['href']
            slug = product_url.strip('/').split('/')[-1]

            products.append({
                'name': name,
                'slug': slug
            })
        except Exception as e:
            logging.warning(f"Error extracting product data: {e}")
            continue

    return products

def scrape_category(category, api_key):
    category_slug = category['slug']
    category_id = category['id']
    category_name = category['name']
    base_url = 'https://www.svx.sk/'
    category_url = urljoin(base_url, category_slug + '/')
    logging.info(f"Scraping category: {category_name} ({category_url})")

    # CSS selector to wait for
    wait_for_selector = '.product-card-wrapper'

    # Fetch the first page to get total number of pages
    html_content = fetch_page(category_url, api_key, wait_for_selector=wait_for_selector)
    soup = BeautifulSoup(html_content, 'html.parser')
    total_pages = get_total_pages(soup)
    logging.info(f"Total pages in category '{category_name}': {total_pages}")

    all_products = []
    for page in range(1, total_pages + 1):
        page_url = f"{category_url}?p={page}"
        logging.info(f"Fetching page {page} of category '{category_name}'")
        html_content = fetch_page(page_url, api_key, wait_for_selector=wait_for_selector)
        soup = BeautifulSoup(html_content, 'html.parser')
        products = extract_products(soup)
        for product in products:
            product['category_id'] = category_id
            product['category_name'] = category_name
            product['category_slug'] = category_slug
        all_products.extend(products)

    logging.info(f"Total products found in category '{category_name}': {len(all_products)}")
    return all_products

def save_products_to_json(products, filename='products.json'):
    data = {
        'fetch_time': datetime.utcnow().isoformat() + 'Z',
        'products': products
    }

    try:
        # Save data to the JSON file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        logging.info(f"Products saved to {filename} with fetch time {data['fetch_time']}.")
    except Exception as e:
        logging.error(f"Failed to save products to JSON. Error: {e}")

# ---------------------- Main Execution ----------------------

if __name__ == "__main__":
    args = parse_arguments()
    CATEGORY_SLUG = args.category_slug
    CATEGORIES_FILE = args.categories
    OUTPUT_FILE = args.output

    # Load categories from the JSON file
    if not os.path.exists(CATEGORIES_FILE):
        logging.error(f"Categories file '{CATEGORIES_FILE}' does not exist.")
        exit(1)

    with open(CATEGORIES_FILE, 'r', encoding='utf-8') as f:
        categories = json.load(f)

    # Check if categories are in a list
    if not isinstance(categories, list):
        logging.error("Categories JSON file should contain a list of categories.")
        exit(1)

    # Find the category with the specified slug
    category_to_scrape = None
    for category in categories:
        if category['slug'] == CATEGORY_SLUG:
            category_to_scrape = category
            break

    if not category_to_scrape:
        logging.error(f"Category with slug '{CATEGORY_SLUG}' not found in '{CATEGORIES_FILE}'.")
        exit(1)

    try:
        products = scrape_category(category_to_scrape, SCRAPER_API_KEY)
        if products:
            logging.info(f"Total products scraped: {len(products)}")
            save_products_to_json(products, OUTPUT_FILE)
        else:
            logging.warning("No products were scraped.")
    except Exception as e:
        logging.error(f"An error occurred while scraping category '{category_to_scrape['name']}': {e}")
