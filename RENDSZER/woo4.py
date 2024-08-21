import json
import requests
import os
import base64
import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from config import api_key
# WooCommerce API credentials
username = 'Deadpool'
password = 'Karategi123'
wp_base_url = 'https://kdtech.hu/wp-json/'
wc_base_url = 'https://kdtech.hu/wp-json/wc/v3/'

# ScraperAPI key

# Encode credentials for HTTP Basic Authentication
auth_string = f'{username}:{password}'
auth_header = {
    'Authorization': 'Basic ' + base64.b64encode(auth_string.encode()).decode()
}

# Function to fetch HTML content using ScraperAPI with delay
def get_html_content(url):
    try:
        print(f"Fetching URL: {url}")
        payload = {
            'api_key': api_key,
            'url': url,
            'render': 'true',
            'device_type': 'desktop',
            'wait_for_selector': 'p[data-delivery-message]'
        }
        response = requests.get('https://api.scraperapi.com/', params=payload)
        response.raise_for_status()
        print("Successfully fetched the URL")
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

# Function to fetch price details from the product page
def fetch_price_details(product_url):
    html_content = get_html_content(product_url)
    if not html_content:
        return None

    soup = BeautifulSoup(html_content, 'html.parser')
    price_details = {}

    # Extracting sale price
    sale_price_tag = soup.find('div', {'data-config-product-price-primary': True})
    if sale_price_tag:
        sale_price = re.sub(r'\D', '', sale_price_tag.text)
        price_details['sale_price'] = float(sale_price)
        print(f"Extracted sale price: {price_details['sale_price']}")

    # Extracting regular price
    regular_price_tag = soup.find('s', {'class': 'mr-8 text-dark-60'})
    if regular_price_tag:
        regular_price = re.sub(r'\D', '', regular_price_tag.text)
        price_details['regular_price'] = float(regular_price)
        print(f"Extracted regular price: {price_details['regular_price']}")

    return price_details

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

# Load the updated JSON file
with open('emelotechnika-kampok-es-lancok-80-es-100-osztaly5.json', 'r', encoding='utf-8') as file:
    products = json.load(file)

# Directory to save downloaded images
save_dir = os.path.join(os.getcwd(), 'images')
os.makedirs(save_dir, exist_ok=True)

# Preprocess product data to ensure correct format
updated_products = []

for product in products:
    # Check if price is missing
    if 'price' not in product or not product['price']:
        # Fetch price details if price is missing
        price_details = fetch_price_details(product['link'])
        if price_details:
            product['regular_price'] = price_details.get('regular_price', 0)
            product['sale_price'] = price_details.get('sale_price', 0)
        else:
            product['regular_price'] = 0
            product['sale_price'] = 0
    else:
        # Convert price to number
        price = product['price']
        price = re.sub(r'\D', '', price)  # Remove all non-numeric characters
        product['regular_price'] = float(price)
        product['sale_price'] = 0

    # Convert weight to a proper decimal number
    weight = product.get('weight')
    if weight:
        weight = weight.replace(',', '.').replace(' g', '').replace('kg', '').strip()
        product['weight'] = float(weight)
    else:
        product['weight'] = None

    updated_products.append(product)

# Save the updated products back to the JSON file
with open('emelotechnika-kampok-es-lancok-80-es-100-osztaly6.json', 'w', encoding='utf-8') as file:
    json.dump(updated_products, file, ensure_ascii=False, indent=4)

# Iterate through the products and upload them to WooCommerce
for product in updated_products:
    image_path = download_image(product['image'], save_dir)
    if image_path:
        image_id, image_url = upload_image(image_path)
        if image_id:
            # Ensure categories are in the correct format
            categories = [{'id': category['id']} for category in product['categories']]
            
            product_data = {
                'name': product['name'],
                'type': 'simple',
                'regular_price': str(product['regular_price']),  # WooCommerce API expects price as a string
                'sale_price': str(product['sale_price']) if product['sale_price'] else '',  # Add sale price if available
                'description': product['description'],
                'short_description': product['short_description'],
                'sku': product['sku'],
                'weight': str(product.get('weight', '')),  # WooCommerce API expects weight as a string
                'dimensions': product['dimensions'],
                'categories': categories,
                'images': [{'id': image_id}],
                'manage_stock': True,
                'stock_quantity': product.get('stock_quantity', 0)  # Default to 0 if not provided
            }
            create_or_update_product_in_woocommerce(product_data)
        os.remove(image_path)  # Remove the downloaded image

print("All products have been uploaded to WooCommerce.")
