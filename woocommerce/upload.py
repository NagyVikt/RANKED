import requests
import json

# WooCommerce REST API credentials
consumer_key = 'ck_a3cce15b0954b01a6093a4273fa403f43bddd1d5'
consumer_secret = 'cs_215e4e6f4bfb6563609aeba59e91ed7905812c86'
store_url = 'https://itrex.hu/'  # Replace with your WooCommerce store URL

# Endpoint for creating new products
endpoint = '/wp-json/wc/v3/products'
url = f"{store_url}{endpoint}"

# Load products from the JSON file
with open('../JSON/products.json', 'r') as file:
    products = json.load(file)

# Function to upload a product to WooCommerce
def upload_product(product_data):
    # Remove 'id' from product_data as it's not needed for creating a new product
    product_data.pop('id', None)

    # Make the API request to create a new product
    response = requests.post(url, auth=(consumer_key, consumer_secret), json=product_data)

    # Check if the request was successful
    if response.status_code == 201:
        print(f"Product '{product_data['name']}' created successfully.")
    else:
        print(f"Failed to create product '{product_data['name']}'. Status Code: {response.status_code}, Response: {response.json()}")

# Iterate over the products and upload each one
for product in products:
    upload_product(product)