import json
import base64
import requests
from urllib.parse import urljoin

# WordPress and WooCommerce API credentials
username = 'Deadpool'
password = 'Karategi123'
wc_base_url = 'https://kdtech.hu/wp-json/wc/v3/'

# Encode credentials for HTTP Basic Authentication
auth_string = f'{username}:{password}'
auth_header = {
    'Authorization': 'Basic ' + base64.b64encode(auth_string.encode()).decode()
}

# Function to get all products
def get_all_products():
    products = []
    page = 1
    while True:
        url = urljoin(wc_base_url, 'products')
        params = {'per_page': 100, 'page': page}
        response = requests.get(url, headers=auth_header, params=params)
        if response.status_code == 200:
            batch = response.json()
            if not batch:
                break
            products.extend(batch)
            page += 1
        else:
            print(f"Failed to retrieve products. Response: {response.text}")
            break
    return products

# Function to update a product in WooCommerce
def update_product(product_id, product_data):
    url = urljoin(wc_base_url, f'products/{product_id}')
    response = requests.put(url, headers=auth_header, json=product_data)
    if response.status_code == 200:
        print(f"Product ID {product_id} updated successfully.")
    else:
        print(f"Failed to update product ID {product_id}. Response: {response.text}")

# Main script execution
if __name__ == "__main__":
    products = get_all_products()
    for product in products:
        description = product.get('description', '')
        if description:
            product_data = {
                "short_description": description
            }
            update_product(product['id'], product_data)
