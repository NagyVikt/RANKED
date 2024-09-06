import json
import requests
import os
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from config.config import api_key
import base64
import re

# WooCommerce API credentials
username = 'Deadpool'
password = 'Karategi123'
wp_base_url = 'https://kdtech.sk/wp-json/'
wc_base_url = 'https://kdtech.sk/wp-json/wc/v3/'

# Encode credentials for HTTP Basic Authentication
auth_string = f'{username}:{password}'
auth_header = {
    'Authorization': 'Basic ' + base64.b64encode(auth_string.encode()).decode()
}

# Function to get HTML content using ScraperAPI
def get_html_content(url):
    try:
        print(f"Fetching URL: {url}")
        
        # Base payload
        payload = {
            'api_key': api_key,
            'url': url,
            'device_type': 'desktop'
        }
        
        response = requests.get('https://api.scraperapi.com/', params=payload)
        response.raise_for_status()
        print("Successfully fetched the URL")
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

# Function to download an image
def download_image(image_url, save_dir):
    response = requests.get(image_url)
    if response.status_code == 200:
        image_name = os.path.basename(urlparse(image_url).path)
        image_path = os.path.join(save_dir, image_name)
        with open(image_path, 'wb') as f:
            f.write(response.content)
        return image_path
    else:
        print(f"Failed to download image {image_url}. Response: {response.text}")
        return None
def fetch_image_and_prices(product_url):
    # Fetch the HTML content using ScraperAPI
    html_content = get_html_content(product_url)
    
    if not html_content:
        return None, None, None
    
    # Parse the HTML using BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # --- Image Scraping ---
    image_url = None
    # Find the <picture> tag and the <img> tag inside it to get the image URL
    picture_tag = soup.find('picture', {'class': 'w-full'})
    if picture_tag:
        img_tag = picture_tag.find('img')
        if img_tag and img_tag.get('src'):
            image_url = img_tag['src']
            # If the src is a relative URL, convert it to absolute
            image_url = urljoin(product_url, image_url)
        else:
            print(f"No image found in the <img> tag on the page {product_url}")
    
    # --- Price Scraping ---
    regular_price = None
    sale_price = None

    # Utility function to clean price strings
    def clean_price(price_str):
        # Extract numeric part of the price
        price = re.findall(r"\d+[\.,]?\d*", price_str)  # Find all numbers with optional decimal
        if price:
            return float(price[0].replace(',', '.'))  # Return the cleaned float
        return None

    # Try to find the regular and sale prices
    regular_price_tag = soup.find('s', {'class': 'mr-8 text-dark-60'})  # Old price (crossed-out price)
    sale_price_tag = soup.find('div', {'data-config-product-price-primary': True})  # Sale price (current price)

    # Case 1: Both regular and sale prices exist
    if regular_price_tag and sale_price_tag:
        # Extract regular price from <s> tag
        regular_price_text = regular_price_tag.get_text(strip=True)
        regular_price = clean_price(regular_price_text)

        # Extract sale price from data-config-product-price-primary
        sale_price_text = sale_price_tag.get_text(strip=True)
        sale_price = clean_price(sale_price_text)

    # Case 2: Only regular price exists (no sale price)
    elif sale_price_tag:
        # In this case, the sale price is actually the regular price
        sale_price_text = sale_price_tag.get_text(strip=True)
        regular_price = clean_price(sale_price_text)

    return image_url, regular_price, sale_price



# Function to upload an image to WordPress
def upload_image(image_path):
    url = urljoin(wp_base_url, 'wp/v2/media')
    headers = {
        'Authorization': auth_header['Authorization'],
        'Content-Disposition': f'attachment; filename={os.path.basename(image_path)}',
    }
    with open(image_path, 'rb') as img:
        files = {'file': img}
        response = requests.post(url, headers=headers, files=files)
    if response.status_code == 201:
        return response.json()['id'], response.json()['source_url']
    else:
        print(f"Failed to upload image {image_path}. Response: {response.text}")
        return None, None

# Function to get a product by SKU from WooCommerce
def get_product_by_sku(sku):
    url = urljoin(wc_base_url, 'products')
    params = {'sku': sku}
    response = requests.get(url, headers=auth_header, params=params)
    if response.status_code == 200:
        products = response.json()
        if products:
            return products[0]  # Return the first matching product
    return None

# Function to create or update a product in WooCommerce
def create_or_update_product_in_woocommerce(product_data):
    existing_product = get_product_by_sku(product_data['sku'])
    if existing_product:
        url = urljoin(wc_base_url, f"products/{existing_product['id']}")
        response = requests.put(url, headers=auth_header, json=product_data)
        if response.status_code == 200:
            print(f"Product '{product_data['name']}' updated successfully.")
            return response.json()
        else:
            print(f"Failed to update product in WooCommerce. Response: {response.text}")
            return None
    else:
        url = urljoin(wc_base_url, 'products')
        response = requests.post(url, headers=auth_header, json=product_data)
        if response.status_code == 201:
            print(f"Product '{product_data['name']}' created successfully.")
            return response.json()
        else:
            print(f"Failed to create product in WooCommerce. Response: {response.text}")
            return None

# Load the JSON file
with open('ochranne-pracovne-prostriedky-delta-plus_new.json', 'r', encoding='utf-8') as file:
    products = json.load(file)

# Directory to save downloaded images
save_dir = os.path.join(os.getcwd(), 'images')
os.makedirs(save_dir, exist_ok=True)

# Iterate through the products and upload them to WooCommerce
for product in products:
    product_url = product.get('link')  # Extract the product URL from the JSON
    
    if not product_url:
        print(f"No product URL found for product {product['name']}. Skipping.")
        continue
    
    image_url, regular_price, sale_price = fetch_image_and_prices(product_url)

    if image_url:
        image_path = download_image(image_url, save_dir)  # Download the image and get the path
        print(f"Image URL: {image_url}")
    if regular_price is not None:
        print(f"Regular Price: {regular_price}")
    if sale_price is not None:
        print(f"Sale Price: {sale_price}")
    
    
    # Upload the image to WooCommerce
    image_id, image_url = upload_image(image_path)
    if image_id:
        # Ensure categories are in the correct format
        categories = [{'id': category['id']} for category in product['categories']]
        
        product_data = {
            'name': product['name'],
            'type': 'simple',
            'regular_price': str(regular_price),  # Use the scraped regular price

            'description': product.get('description', ''),  # Use an empty string if 'description' is missing
            'short_description': product.get('short_description', ''),
            'sku': product['sku'],
            'weight': str(product.get('weight', '')),  # WooCommerce API expects weight as a string
            'dimensions': product.get('dimensions', {}),
            'categories': categories,
            'images': [{'id': image_id}],
            'manage_stock': True,
            'stock_quantity': product.get('stock_quantity', 0)  # Default to 0 if not provided
        }

      # Only add the sale price if it is greater than 0
        if sale_price is not None and sale_price > 0:
            product_data['sale_price'] = str(sale_price)

        
        # Create or update the product in WooCommerce
        create_or_update_product_in_woocommerce(product_data)
        
        # Remove the downloaded image after it has been successfully uploaded
        try:
            os.remove(image_path)
            print(f"Image {image_path} deleted successfully.")
        except OSError as e:
            print(f"Error deleting image {image_path}: {e}")
    else:
        print(f"Failed to upload image for product {product['name']}")

print("All products have been uploaded to WooCommerce.")
