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
        logging.FileHandler("products_upload.log"),
        logging.StreamHandler()
    ]
)

# Load environment variables from a .env file
load_dotenv()

# Fetch API credentials from environment variables

WC_BASE_URL =  'https://www.kdtech.sk/wp-json/wc/v1/'

CONSUMER_KEY = "ck_45468d369e80d13d23f8a0f5adc31cb2dccf0f05"
CONSUMER_SECRET = "cs_fe8b05dcf4471f3364192c098397fbdedeae630c"



if not CONSUMER_KEY or not CONSUMER_SECRET or not WC_BASE_URL:
    logging.error("WooCommerce API credentials or base URL are not set. Please set WC_CONSUMER_KEY, WC_CONSUMER_SECRET, and WC_BASE_URL in your .env file.")
    exit(1)

# Set up OAuth1 authentication
auth = OAuth1(CONSUMER_KEY, CONSUMER_SECRET, signature_method='HMAC-SHA1')

# ---------------------- Argument Parsing ----------------------

def parse_arguments():
    """
    Parses command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(description='Upload products to WooCommerce from a JSON file.')
    parser.add_argument('--json', type=str, default='woocommerce_products_updated.json', help='Path to the JSON file containing products')
    return parser.parse_args()

# ---------------------- Functions ----------------------

def read_products_from_json(json_file):
    """
    Reads products from a JSON file.

    Args:
        json_file (str): Path to the JSON file.

    Returns:
        list: List of product dictionaries.
    """
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Assuming the JSON structure is a list of fetch entries
            all_products = []
            for entry in data:
                products = entry.get('products', [])
                all_products.extend(products)
            logging.info(f"Total products read from JSON: {len(all_products)}")
            return all_products
    except Exception as e:
        logging.error(f"Failed to read products from {json_file}. Error: {e}")
        return []

def get_product_by_id(product_id):
    """
    Retrieves a product from WooCommerce by its ID.

    Args:
        product_id (int): The WooCommerce product ID.

    Returns:
        dict or None: The product data if found, else None.
    """
    url = urljoin(WC_BASE_URL, f'products/{product_id}')
    response = requests.get(url, auth=auth)
    if response.status_code == 200:
        logging.info(f"Product with ID {product_id} exists. It will be updated.")
        return response.json()
    elif response.status_code == 404:
        logging.info(f"Product with ID {product_id} does not exist. It will be created.")
        return None
    else:
        logging.error(f"Failed to retrieve product ID {product_id}. Status Code: {response.status_code}, Response: {response.text}")
        return None

def upload_product(product):
    """
    Uploads a single product to WooCommerce. Updates if exists, else creates.

    Args:
        product (dict): The product data.

    Returns:
        bool: True if upload was successful, False otherwise.
    """
    product_id = product.get('id')
    if not product_id:
        logging.error("Product ID is missing. Skipping product.")
        return False

    existing_product = get_product_by_id(product_id)
    if existing_product:
        # Update existing product
        method = 'PUT'
        endpoint = f'products/{product_id}'
    else:
        # Create new product
        method = 'POST'
        endpoint = 'products'

    url = urljoin(WC_BASE_URL, endpoint)

    # Prepare the product data according to WooCommerce API
    payload = prepare_product_payload(product)

    try:
        if method == 'PUT':
            response = requests.put(url, auth=auth, json=payload)
        else:
            response = requests.post(url, auth=auth, json=payload)

        if response.status_code in [200, 201]:
            logging.info(f"Successfully {'updated' if method == 'PUT' else 'created'} product ID {product_id}.")
            return True
        else:
            logging.error(f"Failed to {'update' if method == 'PUT' else 'create'} product ID {product_id}. Status Code: {response.status_code}, Response: {response.text}")
            return False
    except Exception as e:
        logging.error(f"Exception occurred while uploading product ID {product_id}. Error: {e}")
        return False

def prepare_product_payload(product):
    """
    Prepares the product payload for WooCommerce API.

    Args:
        product (dict): The original product data.

    Returns:
        dict: The payload to send to WooCommerce.
    """
    payload = {
        "id": product.get("id"),
        "name": product.get("name"),
        "slug": product.get("slug"),
        "type": product.get("type"),
        "status": product.get("status"),
        "featured": product.get("featured"),
        "catalog_visibility": product.get("catalog_visibility"),
        "description": product.get("description"),
        "short_description": product.get("short_description"),
        "sku": product.get("sku"),
        "price": product.get("price"),
        "regular_price": product.get("regular_price"),
        "sale_price": product.get("sale_price"),
        "date_on_sale_from": product.get("date_on_sale_from"),
        "date_on_sale_to": product.get("date_on_sale_to"),
        "manage_stock": product.get("manage_stock"),
        "stock_quantity": product.get("stock_quantity"),
        "in_stock": product.get("in_stock"),
        "backorders": product.get("backorders"),
        "sold_individually": product.get("sold_individually"),
        "weight": product.get("weight"),
        "dimensions": product.get("dimensions"),
        "shipping_required": product.get("shipping_required"),
        "shipping_taxable": product.get("shipping_taxable"),
        "shipping_class": product.get("shipping_class"),
        "reviews_allowed": product.get("reviews_allowed"),
        "tax_status": product.get("tax_status"),
        "tax_class": product.get("tax_class"),
        "attributes": product.get("attributes"),
        "default_attributes": product.get("default_attributes"),
        "categories": prepare_categories(product.get("categories", [])),
        "images": prepare_images(product.get("images", [])),
        "tags": product.get("tags", []),
        # Add other fields as necessary
    }

    # Remove keys with empty values to prevent overwriting existing data with empty fields
    payload = {k: v for k, v in payload.items() if v not in [None, "", [], {}, False]}

    return payload

def prepare_categories(categories):
    """
    Prepares the categories payload.

    Args:
        categories (list): List of category dictionaries.

    Returns:
        list: List of categories formatted for WooCommerce API.
    """
    prepared = []
    for cat in categories:
        if isinstance(cat, dict):
            prepared.append({
                "id": cat.get("id"),
                "name": cat.get("name"),
                "slug": cat.get("slug")
            })
    return prepared

def prepare_images(images):
    """
    Prepares the images payload.

    Args:
        images (list): List of image dictionaries.

    Returns:
        list: List of images formatted for WooCommerce API.
    """
    prepared = []
    for img in images:
        if isinstance(img, dict):
            prepared.append({
                "src": img.get("src"),
                "name": img.get("name"),
                "alt": img.get("alt"),
                "position": img.get("position")
            })
    return prepared

def upload_products(products):
    """
    Uploads a list of products to WooCommerce.

    Args:
        products (list): List of product dictionaries.

    Returns:
        dict: Summary of upload results.
    """
    success_count = 0
    failure_count = 0

    for product in products:
        success = upload_product(product)
        if success:
            success_count += 1
        else:
            failure_count += 1

    summary = {
        "total": len(products),
        "successful": success_count,
        "failed": failure_count
    }

    return summary

# ---------------------- Main Execution ----------------------

if __name__ == "__main__":
    args = parse_arguments()
    JSON_FILE = args.json

    logging.info(f"Starting to upload products from {JSON_FILE} to WooCommerce...")

    products = read_products_from_json(JSON_FILE)

    if not products:
        logging.warning("No products to upload. Exiting.")
        exit(0)

    upload_summary = upload_products(products)

    logging.info(f"Upload Summary: Total: {upload_summary['total']}, Successful: {upload_summary['successful']}, Failed: {upload_summary['failed']}")

    logging.info("Product upload process completed.")
