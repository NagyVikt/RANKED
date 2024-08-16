import json
import requests
import os
import base64
from urllib.parse import urljoin, urlparse

# WooCommerce API credentials
username = 'Deadpool'
password = 'Karategi123'
wp_base_url = 'https://kdtech.hu/wp-json/'
wc_base_url = 'https://kdtech.hu/wp-json/wc/v3/'

# Encode credentials for HTTP Basic Authentication
auth_string = f'{username}:{password}'
auth_header = {
    'Authorization': 'Basic ' + base64.b64encode(auth_string.encode()).decode()
}

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
with open('magnesek2.json', 'r', encoding='utf-8') as file:
    products = json.load(file)

# Directory to save downloaded images
save_dir = os.path.join(os.getcwd(), 'images')
os.makedirs(save_dir, exist_ok=True)

# Preprocess product data to ensure correct format
for product in products:
    # Convert price to number
    product['price'] = product['price'].replace(' Ft', '').replace(' ', '')  # Removing 'Ft' and non-breaking space
    product['price'] = float(product['price'])

    # Convert weight to a proper decimal number
    if product['weight']:
        product['weight'] = product['weight'].replace(',', '.').replace(' g', '').replace('kg', '').strip()
        product['weight'] = float(product['weight'])

# Iterate through the products and upload them to WooCommerce
for product in products:
    image_path = download_image(product['image'], save_dir)
    if image_path:
        image_id, image_url = upload_image(image_path)
        if image_id:
            product_data = {
                'name': product['name'],
                'type': 'simple',
                'regular_price': str(product['price']),  # WooCommerce API expects price as a string
                'description': product['description'],
                'short_description': product['short_description'],
                'sku': product['sku'],
                'weight': str(product['weight']),  # WooCommerce API expects weight as a string
                'dimensions': product['dimensions'],
                'categories': [{'id': 82}],  # Assuming 'Uncategorized' category
                'images': [{'id': image_id}],
                'manage_stock': True,
                'stock_quantity': product.get('stock_quantity', 0)  # Default to 0 if not provided
            }
            create_or_update_product_in_woocommerce(product_data)
        os.remove(image_path)  # Remove the downloaded image

print("All products have been uploaded to WooCommerce.")
