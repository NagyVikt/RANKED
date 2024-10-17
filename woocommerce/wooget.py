import json
import requests
from urllib.parse import urljoin
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# WooCommerce API credentials (use environment variables for security)
consumer_key = os.getenv('WC_CONSUMER_KEY')
consumer_secret = os.getenv('WC_CONSUMER_SECRET')
wc_base_url = 'https://kdtech.sk/wp-json/wc/v3/'

if not consumer_key or not consumer_secret:
    logging.error("WooCommerce API credentials are not set. Please set WC_CONSUMER_KEY and WC_CONSUMER_SECRET.")
    exit(1)

# Function to fetch all products from WooCommerce using API keys
def fetch_all_products():
    url = urljoin(wc_base_url, 'products')
    params = {
        'per_page': 100,
        'consumer_key': consumer_key,
        'consumer_secret': consumer_secret
    }
    products = []
    page = 1
    while True:
        params['page'] = page
        response = requests.get(url, params=params)
        if response.status_code == 200:
            products_page = response.json()
            if not products_page:
                break  # No more products to fetch
            products.extend(products_page)
            logging.info(f"Fetched page {page} with {len(products_page)} products.")
            page += 1
        else:
            logging.error(f"Failed to fetch products on page {page}. Response: {response.text}")
            break
    return products

# Function to extract all image URLs from the products
def extract_image_urls(products):
    image_urls = []
    for product in products:
        images = product.get('images', [])
        for image in images:
            src = image.get('src')
            if src:
                image_urls.append(src)
    return image_urls

# Function to save image URLs to a JSON file
def save_image_urls_to_json(image_urls, filename='woo_image_urls.json'):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(image_urls, f, ensure_ascii=False, indent=4)
        logging.info(f"Image URLs saved to {filename}")
    except Exception as e:
        logging.error(f"Failed to save image URLs to JSON. Error: {e}")

# Function to save image URLs to a text file
def save_image_urls_to_txt(image_urls, filename='woo_image_urls.txt'):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            for url in image_urls:
                f.write(url + '\n')
        logging.info(f"Image URLs saved to {filename}")
    except Exception as e:
        logging.error(f"Failed to save image URLs to TXT. Error: {e}")

# Main script execution
if __name__ == "__main__":
    logging.info("Starting to fetch products from WooCommerce...")
    products = fetch_all_products()
    if products:
        logging.info(f"Total products fetched: {len(products)}")
        image_urls = extract_image_urls(products)
        if image_urls:
            logging.info(f"Total image URLs extracted: {len(image_urls)}")
            save_image_urls_to_json(image_urls)
            save_image_urls_to_txt(image_urls)
        else:
            logging.warning("No image URLs found in the fetched products.")
    else:
        logging.warning("No products fetched from WooCommerce.")
