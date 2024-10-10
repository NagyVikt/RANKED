import json
import os
import base64
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

# WordPress and WooCommerce API credentials
username = 'Deadpool'
password = 'Karategi123'
wp_base_url = 'https://kdtech.sk/wp-json/'
wc_base_url = 'https://kdtech.sk/wp-json/wc/v3/'

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

# Function to get a product by ID
def get_product_by_id(product_id):
    url = urljoin(wc_base_url, f'products/{product_id}')
    response = requests.get(url, headers=auth_header)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get product by ID {product_id}. Response: {response.text}")
    return None

# Function to create a product in WooCommerce
def create_product(product_data):
    url = urljoin(wc_base_url, 'products')
    response = requests.post(url, headers=auth_header, json=product_data)
    if response.status_code == 201:
        product_id = response.json()['id']
        print(f"Product {product_data['name']} created successfully with ID {product_id}.")
        return product_id
    else:
        print(f"Failed to create product {product_data['name']}. Response: {response.text}")
        return None

# Function to update a product in WooCommerce
def update_product(product_id, product_data):
    url = urljoin(wc_base_url, f'products/{product_id}')
    response = requests.put(url, headers=auth_header, json=product_data)
    if response.status_code == 200:
        print(f"Product {product_data['name']} updated successfully.")
    else:
        print(f"Failed to update product {product_data['name']}. Response: {response.text}")

# Function to fetch all image URLs from the product page
def fetch_image_urls(product_url):
    response = requests.get(product_url)
    image_urls = []
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        image_tags = soup.select('.glide__bullets .glide__bullet img')
        for img_tag in image_tags:
            img_url = img_tag.get('data-src', img_tag.get('src'))
            if img_url:
                image_urls.append(urljoin(product_url, img_url))
    return image_urls

# Function to read products from JSON file and upload/update to WooCommerce
def upload_products(json_file):
    category_name = os.path.splitext(os.path.basename(json_file))[0]
    image_dir = os.path.join(os.getcwd(), category_name)
    os.makedirs(image_dir, exist_ok=True)

    with open(json_file, 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    for product in products:
        product_id = product.get('woo_id')
        existing_product = get_product_by_id(product_id) if product_id else None
        product_data = {
            'name': product['name'],
            'regular_price': product['price'].replace(' Ft', '').replace(',', ''),
            'stock_quantity': product.get('stock_quantity', 0),
            'manage_stock': True,
            'in_stock': True,
            'description': product['description'],
            'weight': product.get('suly', '').replace(' g', '')
        }

        image_urls = fetch_image_urls(product['link'])
        images = []
        for img_url in image_urls:
            image_path = download_image(img_url, image_dir)
            if image_path:
                image_id, uploaded_image_url = upload_image(image_path)
                if image_id and uploaded_image_url:
                    update_image_metadata(image_id, product['name'])
                    images.append({'id': image_id})
                    os.remove(image_path)  # Remove local image after uploading

        if images:
            product_data['images'] = images

        if existing_product:
            product_id = existing_product['id']
            product_data['short_description'] = existing_product.get('short_description', '')
            update_product(product_id, product_data)
        else:
            product_data.update({
                'type': 'simple',
                'short_description': '',
                'categories': [{'name': category_name}],
                'external_url': product['link']
            })
            product_id = create_product(product_data)

        # Update the JSON with the WooCommerce product ID
        if product_id:
            product['woo_id'] = product_id

    # Save the updated products with WooCommerce IDs back to the JSON file
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=4)

# Main script execution
if __name__ == "__main__":
    json_file = 'woosk.json'  # Replace with your actual JSON file name
    upload_products(json_file)
