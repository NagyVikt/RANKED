import requests
from bs4 import BeautifulSoup
import json
import os
import random
from urllib.parse import urljoin
import logging

# Configuration
base_url = 'https://www.svx.sk'
api_key = '4ce5d066b1d682c4fe042f95ef56fdc5'  # Set your API key here
headers = {'User-Agent': 'Mozilla/5.0'}
used_subcategory_ids = set()

# Configure logging
logging.basicConfig(
    filename='scraper.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Function to fetch a webpage using Scraper API with error logging
def fetch_page(url, api_key):
    try:
        payload = {
            'api_key': api_key,
            'url': url,
            'render': 'true',
            'device_type': 'desktop'
        }
        response = requests.get('http://api.scraperapi.com/', params=payload, headers=headers)
        response.raise_for_status()
        logging.info(f"Successfully fetched {url}")
        return response.text
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching {url}: {e}")
        raise

# Function to parse subcategory URLs from the main category page
def get_subcategory_urls(category_url, api_key):
    html = fetch_page(category_url, api_key)
    soup = BeautifulSoup(html, 'html.parser')
    
    # Get all subcategories, even the collapsed ones
    subcategory_urls = []
    subcategory_tiles = soup.select('li a[href^="/naradie-"]')
    
    for tile in subcategory_tiles:
        href = tile['href']
        subcategory_urls.append(urljoin(base_url, href))
    
    logging.info(f"Found {len(subcategory_urls)} subcategories for {category_url}")
    return subcategory_urls

# Function to extract product information from a subcategory page
def get_products_from_subcategory(subcategory_url, api_key):
    html = fetch_page(subcategory_url, api_key)
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find all product cards based on the new HTML structure
    products = []
    
    # Select the anchor tag that contains the product name within the product card
    product_cards = soup.select('div.inline-flex a')  # Adjusted to match the correct structure

    for card in product_cards:
        # Extract the product name from the <a> tag text
        product_name = card.get_text(strip=True)
        
        # Extract the product URL from the href attribute of the <a> tag
        product_url = card['href']
        full_product_url = urljoin(base_url, product_url)
        
        products.append({'name': product_name, 'url': full_product_url})
    
    logging.info(f"Found {len(products)} products in subcategory {subcategory_url}")
    return products


# Function to generate a unique random subcategory ID (at least three digits)
def generate_subcategory_id():
    while True:
        new_id = random.randint(100, 9999)
        if new_id not in used_subcategory_ids:
            used_subcategory_ids.add(new_id)
            return new_id

# Function to save product information to a JSON file
def save_product_json(product, category, subcategory, output_dir):
    product_data = {
        'name': product['name'],
        'categories': [
            {
                'id': category['id'],
                'name': category['name'],
                'slug': category['slug']
            },
            {
                'id': subcategory['id'],
                'name': subcategory['name'],
                'slug': subcategory['slug']
            }
        ]
    }
    
    # Create the directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Define file path
    file_name = f"subcategories-{subcategory['slug']}.json"
    file_path = os.path.join(output_dir, file_name)
    
    # Load existing data if the file exists
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as json_file:
                data = json.load(json_file)
        except json.JSONDecodeError:
            logging.warning(f"JSON decoding error in {file_path}, creating a new file.")
            data = []
    else:
        data = []
    
    # Append new product and save back to JSON file
    data.append(product_data)
    with open(file_path, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)
    
    logging.info(f"Saved product {product['name']} to {file_path}")

# Main function to process the category
def process_category(category_url, category_info, api_key, output_dir):
    try:
        subcategory_urls = get_subcategory_urls(category_url, api_key)
        
        for subcategory_url in subcategory_urls:
            subcategory_slug = subcategory_url.rstrip('/').split('/')[-1]
            subcategory_name = subcategory_slug.replace('-', ' ').title()
            subcategory_info = {
                'id': generate_subcategory_id(),
                'name': subcategory_name,
                'slug': subcategory_slug
            }
            
            # Get products from this subcategory
            products = get_products_from_subcategory(subcategory_url, api_key)
            
            # Save each product in this subcategory to a JSON file as soon as it's processed
            for product in products:
                save_product_json(product, category_info, subcategory_info, output_dir)
    
    except Exception as e:
        logging.error(f"Error processing category {category_url}: {e}")
        raise

# Example usage
category_info = {
    "id": 97,
    "name": "Náradie",
    "slug": "naradie"
}

# Define the category URL and output directory
category_url = "https://www.svx.sk/naradie/"
output_dir = "subcategories-naradie"

# Start processing the category
process_category(category_url, category_info, api_key, output_dir)
