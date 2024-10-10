import requests
import json
import base64

# WooCommerce API credentials
username = 'Deadpool'  # Replace with your WooCommerce username
password = 'Karategi123'  # Replace with your WooCommerce password
wc_base_url = 'https://kdtech.sk/wp-json/wc/v3/'

# Encode credentials for HTTP Basic Authentication
auth_string = f'{username}:{password}'
auth_header = {
    'Authorization': 'Basic ' + base64.b64encode(auth_string.encode()).decode()
}

# Initialize an empty list to store all products
all_products = []

# Parameters for pagination
per_page = 100  # Maximum per_page is 100
page = 1

while True:
    print(f"Fetching page {page}...")
    response = requests.get(
        wc_base_url + 'products',
        headers=auth_header,
        params={
            'per_page': per_page,
            'page': page
        }
    )

    if response.status_code != 200:
        print(f"Failed to fetch products: {response.text}")
        break

    products = response.json()
    if not products:
        # No more products to fetch
        break

    all_products.extend(products)
    page += 1

print(f"Total products fetched: {len(all_products)}")

# Save the products to a JSON file
with open('woocommerce_products.json', 'w', encoding='utf-8') as f:
    json.dump(all_products, f, ensure_ascii=False, indent=4)

print("Products saved to 'woocommerce_products.json'")
