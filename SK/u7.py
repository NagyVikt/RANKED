import requests
from bs4 import BeautifulSoup
import json
import base64
import re
from config.config import api_key

# Function to get product information from the URL
def get_product_info(url, api_key):
    # Base payload for Scraper API
    payload = {
        'api_key': api_key,
        'url': url,
        'render': 'true',
        'device_type': 'desktop'
    }

    # Fetch the page using the Scraper API
    response = requests.get('http://api.scraperapi.com/', params=payload)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch page: {response.status_code}")

    html = response.text

    # Parse the HTML with BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')

    # Extract the product description
    description_div = soup.find('div', id='product-description-tab-content')
    if description_div:
        # Clean and extract text from the description
        description_text = description_div.get_text(separator='\n').strip()
    else:
        description_text = ''

    # Extract the specifications
    specs = {}
    specs_div = soup.find('div', id='product-specifications-tab-content')
    if specs_div:
        for li in specs_div.find_all('li'):
            # Each 'li' contains the label and the value
            label_div = li.find('div', class_='w-full sm:w-1/2')
            value_div = li.find('div', class_='w-full max-sm:text-p-small sm:w-1/2')
            if label_div and value_div:
                label = label_div.get_text(strip=True)
                value = value_div.get_text(strip=True)

                # Mapping various parameters
                if 'Šírka' in label:
                    specs['width'] = value.replace('mm', '').strip()
                elif 'Dĺžka' in label:
                    specs['length'] = value.replace('cm', '').strip()
                elif 'Výška' in label:
                    specs['height'] = value.replace('mm', '').strip()
                elif 'Váha' in label or 'Hmotnosť' in label:
                    specs['weight'] = value.replace('kg', '').strip()
                elif 'Materiál' in label:
                    specs['material'] = value.strip()
                elif 'Variant' in label:
                    specs['Variant'] = value.strip()
                elif 'Objem (ml)' in label:
                    specs['Objem (ml)'] = value.strip()
                elif 'Typ látky' in label:
                    specs['Typ látky'] = value.strip()
                else:
                    # Handle other specs or ignore them
                    specs[label] = value.strip()
    else:
        specs['error'] = 'Specifications not found.'

    return {
        'description': description_text,
        'specs': specs
    }

# WooCommerce API credentials
username = 'Deadpool'
password = 'Karategi123'
wc_base_url = 'https://kdtech.sk/wp-json/wc/v3/'

# Read the product list from the JSON file
with open('rebriky-alve.json', 'r', encoding='utf-8') as f:
    products = json.load(f)

# Iterate over each product
for product in products:
    try:
        # Get the product link and SKU
        url = product.get('link')
        sku = product.get('sku')

        if not url or not sku:
            print(f"Skipping product due to missing URL or SKU: {product.get('name')}")
            continue

        # Scrape the product information
        product_info = get_product_info(url, api_key)

        # Prepare the product data for WooCommerce
        product_data = {
            'description': product_info['description'],  # Use the scraped description
        }

        # Construct the short description from specific specs
        short_description = ''
        fields = ['Objem (ml)', 'Typ látky', 'Variant']
        for field in fields:
            if field in product_info['specs']:
                short_description += f"<p><strong>{field}:</strong> {product_info['specs'][field]}</p>\n"

        # Set the short description
        product_data['short_description'] = short_description.strip()

        # Handle weight
        weight = product_info['specs'].get('weight', '')
        if weight:
            product_data['weight'] = weight

        # Handle dimensions
        dimensions = {}
        length = product_info['specs'].get('length', '')
        width = product_info['specs'].get('width', '')
        height = product_info['specs'].get('height', '')

        if length:
            dimensions['length'] = length
        if width:
            dimensions['width'] = width
        if height:
            dimensions['height'] = height

        if dimensions:
            product_data['dimensions'] = dimensions

        # Get the product ID from WooCommerce using SKU
        response = requests.get(
            wc_base_url + "products",
            params={'sku': sku},
            auth=(username, password)
        )

        if response.status_code != 200:
            print(f"Failed to get product with SKU '{sku}': {response.text}")
            continue

        products_data = response.json()
        if not products_data:
            print(f"No product found with SKU '{sku}'")
            continue

        # Assuming only one product matches the SKU
        product_id = products_data[0]['id']

        # Update the product in WooCommerce
        print(f"Updating product ID {product_id} with SKU {sku}")
        update_response = requests.put(
            wc_base_url + f"products/{product_id}",
            json=product_data,
            auth=(username, password)
        )

        if update_response.status_code in [200, 201]:
            print(f"Product '{product.get('name')}' updated successfully.")
        else:
            print(f"Failed to update product '{product.get('name')}': {update_response.text}")

    except Exception as e:
        print(f"Error processing product '{product.get('name')}': {str(e)}")
