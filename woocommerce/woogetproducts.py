import json
import os
import base64
import requests
from urllib.parse import urljoin
import re

# WordPress and WooCommerce API credentials
username = 'Deadpool'
password = 'Karategi123'
wc_base_url = 'https://kdtech.sk/wp-json/wc/v3/'

# Encode credentials for HTTP Basic Authentication
auth_string = f'{username}:{password}'
auth_header = {
    'Authorization': 'Basic ' + base64.b64encode(auth_string.encode()).decode()
}

# Function to get all categories from WooCommerce
def get_all_categories():
    url = urljoin(wc_base_url, 'products/categories')
    response = requests.get(url, headers=auth_header)
    if response.status_code == 200:
        categories = response.json()
        return categories
    else:
        print(f"Failed to fetch categories. Response: {response.text}")
        return []

# Function to create a new category in WooCommerce
def create_category(name, slug):
    url = urljoin(wc_base_url, 'products/categories')
    category_data = {
        'name': name,
        'slug': slug
    }
    response = requests.post(url, headers=auth_header, json=category_data)
    if response.status_code == 201:
        print(f"Category '{name}' created successfully.")
        return response.json()['id']
    else:
        print(f"Failed to create category '{name}'. Response: {response.text}")
        return None

# Function to get category ID by name, or create it if it doesn't exist
def get_or_create_category_id(category_name, category_slug):
    categories = get_all_categories()
    for category in categories:
        if category['name'] == category_name:
            return category['id']
    return create_category(category_name, category_slug)

# Function to get all products from WooCommerce
def get_all_products():
    products = []
    page = 1
    while True:
        url = urljoin(wc_base_url, 'products')
        params = {'per_page': 100, 'page': page}
        response = requests.get(url, headers=auth_header, params=params)
        if response.status_code == 200:
            page_products = response.json()
            if not page_products:
                break
            products.extend(page_products)
            page += 1
        else:
            print(f"Failed to fetch products. Response: {response.text}")
            break
    return products

# Function to update a product's short description and dimensions in WooCommerce
def update_product(product_id, short_description, dimensions, category_id):
    url = urljoin(wc_base_url, f'products/{product_id}')
    product_data = {
        'short_description': short_description,
        'dimensions': dimensions,
        'categories': [{'id': category_id}]
    }
    response = requests.put(url, headers=auth_header, json=product_data)
    if response.status_code == 200:
        print(f"Product ID {product_id} updated successfully.")
    else:
        print(f"Failed to update product ID {product_id}. Response: {response.text}")

# Function to read products from JSON file and update short descriptions and dimensions in WooCommerce
def update_products_from_json(json_file, category_id):
    with open(json_file, 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    existing_products = get_all_products()
    
    updated_products = []

    for product in products:
        matching_product = next((p for p in existing_products if p['name'] == product['name']), None)
        if matching_product:
            short_description = ' '.join(product['attributes'])
            
            # Extract dimensions from short description
            width = ''
            height = ''
            for attr in product['attributes']:
                if 'Átmérő' in attr:
                    width = re.search(r'(\d+)', attr).group(1)
                if 'Magasság' in attr:
                    height = re.search(r'(\d+)', attr).group(1)
            
            dimensions = {
                'length': '',
                'width': width,
                'height': height
            }
            
            update_product(matching_product['id'], short_description, dimensions, category_id)
            matching_product['short_description'] = short_description
            matching_product['dimensions'] = dimensions
            updated_products.append(matching_product)

    return updated_products

# Main script execution
if __name__ == "__main__":
    json_file = 'magnesek.json'  # Replace with your actual JSON file name
    category_name = 'Mágnesek'
    category_slug = 'magnesek'
    
    category_id = get_or_create_category_id(category_name, category_slug)

    if category_id:
        updated_products = update_products_from_json(json_file, category_id)

        # Save updated products to a new JSON file
        with open('updated_products.json', 'w', encoding='utf-8') as f:
            json.dump(updated_products, f, ensure_ascii=False, indent=4)
        
        print(f"Updated products saved to updated_products.json")
