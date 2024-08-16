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

# Function to fetch all products from WooCommerce
def fetch_all_products():
    url = urljoin(wc_base_url, 'products')
    params = {'per_page': 100}  # Set per_page to 100 to get the maximum number of products per request
    products = []
    while True:
        response = requests.get(url, headers=auth_header, params=params)
        if response.status_code == 200:
            products_page = response.json()
            if not products_page:
                break  # No more products to fetch
            products.extend(products_page)
            params['page'] = params.get('page', 1) + 1  # Move to the next page
        else:
            print(f"Failed to fetch products. Response: {response.text}")
            break
    return products

# Function to save products to a JSON file
def save_products_to_json(products, filename='woo_products.json'):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=4)
    print(f"Products saved to {filename}")

# Main script execution
if __name__ == "__main__":
    products = fetch_all_products()
    save_products_to_json(products)
