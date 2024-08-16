import base64
import requests
from urllib.parse import urljoin

# WooCommerce API credentials
username = 'Deadpool'
password = 'Karategi123'
wc_base_url = 'https://kdtech.hu/wp-json/wc/v3/'

# Encode credentials for HTTP Basic Authentication
auth_string = f'{username}:{password}'
auth_header = {
    'Authorization': 'Basic ' + base64.b64encode(auth_string.encode()).decode()
}

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

# Function to delete a product by ID
def delete_product(product_id):
    url = urljoin(wc_base_url, f'products/{product_id}')
    response = requests.delete(url, headers=auth_header, params={'force': True})
    if response.status_code == 200:
        print(f"Product ID {product_id} deleted successfully.")
    else:
        print(f"Failed to delete product ID {product_id}. Response: {response.text}")

# Function to delete all products
def delete_all_products():
    products = get_all_products()
    for product in products:
        delete_product(product['id'])

# Main script execution
if __name__ == "__main__":
    delete_all_products()
