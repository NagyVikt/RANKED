import json
import os
import requests
from urllib.parse import urljoin
import logging
from datetime import datetime
import argparse
from dotenv import load_dotenv
from requests_oauthlib import OAuth1

# ---------------------- Configuration and Setup ----------------------

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("products_fetch.log"),
        logging.StreamHandler()
    ]
)

# Load environment variables from a .env file
load_dotenv()

# Fetch API credentials from environment variables
# Fetch API credentials from environment variables
CONSUMER_KEY = "ck_45468d369e80d13d23f8a0f5adc31cb2dccf0f05"
CONSUMER_SECRET = "cs_fe8b05dcf4471f3364192c098397fbdedeae630c"

if not CONSUMER_KEY or not CONSUMER_SECRET:
    logging.error("WooCommerce API credentials are not set. Please set WC_CONSUMER_KEY and WC_CONSUMER_SECRET in your .env file.")
    exit(1)

# Your WooCommerce site URL
wc_base_url = 'https://www.kdtech.sk/wp-json/wc/v1/'

# Set up OAuth1 authentication
auth = OAuth1(CONSUMER_KEY, CONSUMER_SECRET, signature_method='HMAC-SHA1')

# ---------------------- Argument Parsing ----------------------

def parse_arguments():
    """
    Parses command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(description='Fetch and save WooCommerce products information.')
    parser.add_argument('--per_page', type=int, default=100, help='Number of products per page (max 100)')
    parser.add_argument('--json', type=str, default='woocommerce_products.json', help='Filename for JSON output')
    return parser.parse_args()

# ---------------------- Functions ----------------------

def get_all_products(per_page=100):
    """
    Fetches all products from WooCommerce.

    Args:
        per_page (int): Number of products per page (max 100).

    Returns:
        list: List of all products.
    """
    url = urljoin(wc_base_url, 'products')
    products = []
    page = 1
    total_pages = None

    while True:
        logging.info(f"Fetching page {page}...")
        params = {
            'per_page': per_page,
            'page': page
        }
        response = requests.get(url, auth=auth, params=params)

        if response.status_code == 200:
            page_products = response.json()
            if not page_products:
                logging.info("No more products to fetch.")
                break

            products.extend(page_products)
            logging.info(f"Fetched {len(page_products)} products from page {page}.")

            if total_pages is None:
                try:
                    total_pages = int(response.headers.get('X-WP-TotalPages', 1))
                    logging.info(f"Total pages to fetch: {total_pages}")
                except (TypeError, ValueError):
                    logging.warning("Unable to retrieve total pages from headers. Continuing until no products are returned.")
                    total_pages = None

            if total_pages and page >= total_pages:
                logging.info("Fetched all available pages.")
                break

            page += 1
        else:
            logging.error(f"Failed to fetch products: {response.status_code} - {response.text}")
            break

    return products

def save_products_to_json(products, filename='woocommerce_products.json'):
    """
    Saves products data to a JSON file with a fetch timestamp.

    Args:
        products (list): List of products to save.
        filename (str): Filename for JSON output.
    """
    data = {
        'fetch_time': datetime.utcnow().isoformat() + 'Z',
        'products': products
    }

    try:
        # Read existing data if file exists
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        else:
            existing_data = []

        # Append new fetch data
        existing_data.append(data)

        # Save back to the JSON file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=4)

        logging.info(f"Products saved to {filename} with fetch time {data['fetch_time']}.")
    except Exception as e:
        logging.error(f"Failed to save products to JSON. Error: {e}")

# ---------------------- Main Execution ----------------------

if __name__ == "__main__":
    args = parse_arguments()
    PER_PAGE = args.per_page
    JSON_FILENAME = args.json

    logging.info(f"Starting to fetch WooCommerce products with {PER_PAGE} products per page...")
    all_products = get_all_products(per_page=PER_PAGE)

    if all_products:
        logging.info(f"Total products fetched: {len(all_products)}")
        save_products_to_json(all_products, JSON_FILENAME)
    else:
        logging.warning("No products fetched from WooCommerce.")
