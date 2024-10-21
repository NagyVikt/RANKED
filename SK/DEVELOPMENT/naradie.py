import os
import json
import requests
from bs4 import BeautifulSoup
from config.config import api_key

# WooCommerce API credentials
WC_BASE_URL = 'https://www.kdtech.sk/wp-json/wc/v3/'  # Use v3 for the latest API
CONSUMER_KEY = "ck_45468d369e80d13d23f8a0f5adc31cb2dccf0f05"
CONSUMER_SECRET = "cs_fe8b05dcf4471f3364192c098397fbdedeae630c"

# Base URL
BASE_URL = "https://www.svx.sk"

def get_html_content(url, wait_for_selector=None):
    """
    Fetches the HTML content of a given URL using ScraperAPI.

    Args:
        url (str): The URL to fetch.
        wait_for_selector (str, optional): CSS selector to wait for before rendering.

    Returns:
        str or None: The HTML content if successful, else None.
    """
    try:
        print(f"Fetching URL: {url}")

        # Base payload
        payload = {
            'api_key': api_key,
            'url': url,
            'render': 'true',
            'device_type': 'desktop'
        }

        # Add wait_for_selector if provided
        if wait_for_selector:
            payload['wait_for_selector'] = wait_for_selector

        response = requests.get('https://api.scraperapi.com/', params=payload)
        response.raise_for_status()
        print("Successfully fetched the URL")
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def get_category_by_slug(slug):
    """
    Checks if a category with the given slug exists in WooCommerce.

    Args:
        slug (str): The slug of the category to check.

    Returns:
        dict or None: The category data if found, else None.
    """
    url = f"{WC_BASE_URL}products/categories"
    params = {'slug': slug}
    try:
        response = requests.get(url, params=params, auth=(CONSUMER_KEY, CONSUMER_SECRET))
        response.raise_for_status()
        categories = response.json()
        if categories:
            return categories[0]  # Return the first matching category
        else:
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching category '{slug}' from WooCommerce: {e}")
        return None

def create_category(name, slug, parent_id=None):
    """
    Creates a new category in WooCommerce.

    Args:
        name (str): The name of the category.
        slug (str): The slug of the category.
        parent_id (int, optional): The ID of the parent category.

    Returns:
        dict or None: The created category data if successful, else None.
    """
    url = f"{WC_BASE_URL}products/categories"
    data = {
        'name': name,
        'slug': slug
    }
    if parent_id:
        data['parent'] = parent_id
    try:
        response = requests.post(url, json=data, auth=(CONSUMER_KEY, CONSUMER_SECRET))
        response.raise_for_status()
        category = response.json()
        print(f"Created new category '{name}' with ID {category['id']}.")
        return category
    except requests.exceptions.RequestException as e:
        print(f"Error creating category '{name}' in WooCommerce: {e}")
        return None


def scrape_categories(category_url, parent_wc_id=None):
    # Fetch the category page
    html_content = get_html_content(category_url)
    if not html_content:
        print(f"Failed to retrieve category page '{category_url}'. Exiting.")
        return None

    soup = BeautifulSoup(html_content, 'html.parser')

    # Get the category slug from the URL
    slug = category_url.strip('/').split('/')[-1]

    # Find the category name
    h1_tag = soup.find('h1')
    if h1_tag:
        name = h1_tag.get_text(strip=True)
    else:
        name = slug.replace('-', ' ').title()

    # Initialize image URL
    img_url = ''

    # Check if the category exists in WooCommerce
    wc_category = get_category_by_slug(slug)
    if wc_category:
        category_id = wc_category['id']
        print(f"Category '{name}' already exists in WooCommerce with ID {category_id}.")
    else:
        # Create the category in WooCommerce
        wc_category = create_category(name=name, slug=slug, parent_id=parent_wc_id)
        if wc_category:
            category_id = wc_category['id']
        else:
            print(f"Failed to create category '{name}' in WooCommerce.")
            return None

    # Build the category dictionary
    category_dict = {
        "id": category_id,
        "slug": slug,
        "name": name,
        "img": img_url,
        "link": f"https://kdtech.sk/shop/?filter_cat={slug}",
        "subcategories": []
    }

    # Check if there are subcategories
    ul = soup.find('ul', class_='catalog__category-tiles')
    if ul:
        # Process subcategories
        for li in ul.find_all('li'):
            a_tag = li.find('a', href=True)
            if not a_tag:
                continue

            subcategory_href = a_tag['href']
            subcategory_url = subcategory_href if subcategory_href.startswith('http') else BASE_URL + subcategory_href

            # Extract subcategory name
            subcategory_name_tag = a_tag.find('div', class_='px-16')
            if subcategory_name_tag:
                subcategory_name = subcategory_name_tag.get_text(strip=True)
            else:
                subcategory_name = subcategory_href.strip('/').split('/')[-1].replace('-', ' ').title()

            # Extract image URL
            img_tag = a_tag.find('img')
            if img_tag:
                img_src = img_tag.get('src')
                if img_src:
                    img_url = img_src if img_src.startswith('http') else BASE_URL + img_src
                else:
                    img_url = ''
            else:
                img_url = ''

            # Check if the subcategory exists in WooCommerce
            subcategory_slug = subcategory_href.strip('/').split('/')[-1]
            wc_subcategory = get_category_by_slug(subcategory_slug)
            if wc_subcategory:
                subcategory_id = wc_subcategory['id']
                print(f"Subcategory '{subcategory_name}' already exists in WooCommerce with ID {subcategory_id}.")
            else:
                # Create the subcategory in WooCommerce
                wc_subcategory = create_category(name=subcategory_name, slug=subcategory_slug, parent_id=category_id)
                if wc_subcategory:
                    subcategory_id = wc_subcategory['id']
                else:
                    print(f"Failed to create subcategory '{subcategory_name}' in WooCommerce.")
                    continue

            # Build the subcategory dictionary
            subcategory_dict = {
                "id": subcategory_id,
                "slug": subcategory_slug,
                "name": subcategory_name,
                "img": img_url,
                "link": f"https://kdtech.sk/shop/?filter_cat={subcategory_slug}",
                "subcategories": []
            }

            # Recursively scrape the subcategory
            deeper_subcategory_dict = scrape_categories(subcategory_url, parent_wc_id=subcategory_id)
            if deeper_subcategory_dict:
                subcategory_dict['subcategories'] = deeper_subcategory_dict.get('subcategories', [])

            category_dict['subcategories'].append(subcategory_dict)
    else:
        # Handle categories without subcategories
        print(f"No subcategories found for category '{name}'.")

    return category_dict


def create_main_category_json(category_data, output_file):
    """
    Writes the category data to a JSON file.

    Args:
        category_data (dict): The category information.
        output_file (str): Path to the output JSON file.
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as outfile:
            json.dump(category_data, outfile, ensure_ascii=False, indent=4)
        print(f"Category JSON has been successfully created at '{output_file}'.")
    except Exception as e:
        print(f"Error writing to '{output_file}': {e}")

def main():
    # Define the main category data
    main_category_url = "https://www.svx.sk/naradie"

    # Start scraping from the main category
    print("Starting to scrape categories and subcategories...")
    category_data = scrape_categories(main_category_url)

    if category_data:
        # Create the JSON output
        output_file = "naradie.json"
        print("\nCreating main category JSON...")
        create_main_category_json(category_data, output_file)
    else:
        print("Failed to scrape the main category.")

if __name__ == "__main__":
    main()
