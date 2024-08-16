import json
import os
import base64
import requests
from urllib.parse import urljoin, urlparse

# WordPress and WooCommerce API credentials
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

# Function to update image metadata
def update_image_metadata(image_id, alt_text):
    url = urljoin(wp_base_url, f'wp/v2/media/{image_id}')
    headers = {
        'Authorization': auth_header['Authorization']
    }
    data = {
        'alt_text': alt_text,
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        print(f"Image metadata for ID {image_id} updated successfully.")
    else:
        print(f"Failed to update image metadata for ID {image_id}. Response: {response.text}")

# Function to get a product by name
def get_product_by_name(product_name):
    url = urljoin(wc_base_url, 'products')
    params = {'search': product_name}
    response = requests.get(url, headers=auth_header, params=params)
    if response.status_code == 200:
        products = response.json()
        if products:
            return products[0]  # Return the first matching product
    else:
        print(f"Failed to search product {product_name}. Response: {response.text}")
    return None

# Function to create a product in WooCommerce
def create_product(product_data):
    url = urljoin(wc_base_url, 'products')
    response = requests.post(url, headers=auth_header, json=product_data)
    if response.status_code == 201:
        print(f"Product {product_data['name']} created successfully.")
    else:
        print(f"Failed to create product {product_data['name']}. Response: {response.text}")

# Function to update a product in WooCommerce
def update_product(product_id, product_data):
    url = urljoin(wc_base_url, f'products/{product_id}')
    response = requests.put(url, headers=auth_header, json=product_data)
    if response.status_code == 200:
        print(f"Product {product_data['name']} updated successfully.")
    else:
        print(f"Failed to update product {product_data['name']}. Response: {response.text}")

# Function to read products from JSON file and upload/update to WooCommerce
def upload_products(json_file):
    category_name = os.path.splitext(os.path.basename(json_file))[0]
    image_dir = os.path.join(os.getcwd(), category_name)
    os.makedirs(image_dir, exist_ok=True)

    with open(json_file, 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    for product in products:
        existing_product = get_product_by_name(product['name'])
        product_data = {
            'name': product['name'],
            'regular_price': product['price'].replace(' Ft', ''),
            'stock_quantity': 500,  # Default stock quantity
            'manage_stock': True,
            'in_stock': True
        }
        if existing_product:
            update_product(existing_product['id'], product_data)
        else:
            image_path = download_image(product['image'], image_dir)
            if image_path:
                image_id, uploaded_image_url = upload_image(image_path)
                if image_id and uploaded_image_url:
                    update_image_metadata(image_id, product['name'])  # Optional: update image metadata
                    product_data.update({
                        'type': 'simple',
                        'description': ' '.join(product['attributes']),
                        'short_description': '',
                        'categories': [{'name': category_name}],  # Use category name from JSON file
                        'images': [{'id': image_id}],  # Use image ID instead of URL
                        'external_url': product['link']
                    })
                    create_product(product_data)

# Main script execution
if __name__ == "__main__":
    json_file = 'magnesek.json'  # Replace with your actual JSON file name
    upload_products(json_file)
