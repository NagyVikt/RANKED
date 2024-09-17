import json
import requests
import os
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import base64
import re

# WooCommerce API credentials
username = 'Deadpool'
password = 'Karategi123'
wp_base_url = 'https://kdtech.sk/wp-json/'
wc_base_url = 'https://kdtech.sk/wp-json/wc/v3/'

# Encode credentials for HTTP Basic Authentication
auth_string = f'{username}:{password}'
auth_header = {
    'Authorization': 'Basic ' + base64.b64encode(auth_string.encode()).decode()
}


# Function to get a product by SKU from WooCommerce
def get_product_by_sku(sku):
    url = urljoin(wc_base_url, 'products')
    params = {'sku': sku}
    response = requests.get(url, headers=auth_header, params=params)
    if response.status_code == 200:
        products = response.json()
        if products:
            return products[0]  # Return the first matching product
    else:
        print(f"Failed to fetch product by SKU. Response: {response.text}")
    return None

# Function to create or update a product in WooCommerce
def create_or_update_product_in_woocommerce(product_data):
    # Check if the product already exists by SKU
    existing_product = get_product_by_sku(product_data['sku'])
    
    # If the product exists, update it
    if existing_product:
        product_id = existing_product['id']
        update_url = urljoin(wc_base_url, f"products/{product_id}")
        
        # Update the existing product
        response = requests.put(update_url, headers=auth_header, json=product_data)
        if response.status_code == 200:
            print(f"Product '{product_data['name']}' (SKU: {product_data['sku']}) updated successfully.")
            return response.json()
        else:
            print(f"Failed to update product (SKU: {product_data['sku']}). Response: {response.text}")
            return None
    
    # If the product does not exist, create a new one
    else:
        create_url = urljoin(wc_base_url, 'products')
        
        # Create the new product
        response = requests.post(create_url, headers=auth_header, json=product_data)
        if response.status_code == 201:
            print(f"Product '{product_data['name']}' (SKU: {product_data['sku']}) created successfully.")
            return response.json()
        else:
            print(f"Failed to create product (SKU: {product_data['sku']}). Response: {response.text}")
            return None


# Function to get HTML content using ScraperAPI
def get_html_content(url):
    try:
        print(f"Fetching URL: {url}")
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

# Function to scrape product specifications (Technické parametre)
def scrape_product_specifications(soup):
    specs = {}
    spec_list = soup.find('div', {'id': 'product-specifications-tab-content'})
    
    if spec_list:
        for item in spec_list.find_all('li', class_='py-16 border-b border-light-material'):
            label = item.find('div', class_='w-full sm:w-1/2').get_text(strip=True)
            value = item.find('div', class_='w-full sm:w-1/2').find('span').get_text(strip=True)

            # Mapping various parameters
            if 'Šírka' in label:
                specs['width'] = value.replace('mm', '').strip()
            elif 'Dĺžka' in label:
                specs['length'] = value.replace('m', '').replace('cm', '').strip()
            elif 'Výška' in label:
                specs['height'] = value.replace('mm', '').strip()
            elif 'Váha' in label or 'Hmotnosť' in label:
                specs['weight'] = value.replace('kg', '').strip()
            elif 'Materiál' in label:
                specs['material'] = value.strip()
            elif 'Variant' in label:
                specs['variant'] = value.strip()
            elif 'Nosnosť' in label:
                specs['capacity'] = value.strip()
            elif 'Farba' in label:
                specs['color'] = value.strip()
                
    return specs

# Function to scrape product description and short description
def scrape_descriptions(soup):
    description = ""
    short_description = ""
    
    description_tag = soup.find('div', class_='rich-text w-8/12 max-sm:w-full')
    if description_tag:
        description = description_tag.get_text(separator="\n", strip=True)
    
    # Assuming that 'short_description' can be fetched or derived
    short_description_tag = soup.find('div', class_='short-description')
    if short_description_tag:
        short_description = short_description_tag.get_text(separator="\n", strip=True)
    else:
        # Fallback if no explicit short description is found
        short_description = description[:150] + "..."
    
    return description, short_description

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

# Function to fetch product price, description, specifications, and short description
def fetch_image_prices_specs_desc(product_url):
    # Fetch the HTML content using ScraperAPI
    html_content = get_html_content(product_url)
    
    if not html_content:
        return None, None, None, None, None, None
    
    # Parse the HTML using BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')

    # --- Price Scraping ---
    regular_price = None
    sale_price = None

    def clean_price(price_str):
        price = re.findall(r"\d+[\.,]?\d*", price_str)
        if price:
            return float(price[0].replace(',', '.'))
        return None

    regular_price_tag = soup.find('s', {'class': 'mr-8 text-dark-60'})
    sale_price_tag = soup.find('div', {'data-config-product-price-primary': True})

    if regular_price_tag and sale_price_tag:
        regular_price = clean_price(regular_price_tag.get_text(strip=True))
        sale_price = clean_price(sale_price_tag.get_text(strip=True))
    elif sale_price_tag:
        regular_price = clean_price(sale_price_tag.get_text(strip=True))

    # --- Specifications Scraping ---
    specifications = scrape_product_specifications(soup)

    # --- Description Scraping ---
    description, short_description = scrape_descriptions(soup)

    return regular_price, sale_price, specifications, description, short_description

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

# Load the JSON file
with open('domacnost-a-drogeria_new.json', 'r', encoding='utf-8') as file:
    products = json.load(file)

# Directory to save downloaded images
save_dir = os.path.join(os.getcwd(), 'images')
os.makedirs(save_dir, exist_ok=True)

# Iterate through the products and upload them to WooCommerce
for product in products:
    product_url = product.get('link')
    
    if not product_url:
        print(f"No product URL found for product {product['name']}. Skipping.")
        continue
    
    regular_price, sale_price, specs, description, short_description = fetch_image_prices_specs_desc(product_url)

    if regular_price is not None:
        print(f"Regular Price: {regular_price}")
    if sale_price is not None:
        print(f"Sale Price: {sale_price}")
    if specs:
        print(f"Specifications: {specs}")
    if description:
        print(f"Description: {description}")
    if short_description:
        print(f"Short Description: {short_description}")
    
    # Prepare the product data for WooCommerce
    categories = [{'id': category['id']} for category in product['categories']]
    
    product_data = {
        'name': product['name'],
        'type': 'simple',
        'regular_price': str(regular_price),
        'description': description,  # Full description
        'short_description': short_description,  # Short description
        'sku': product['sku'],
        'weight': specs.get('weight', ''),
        'dimensions': {
            'length': specs.get('length', ''),
            'width': specs.get('width', ''),
            'height': specs.get('height', '')
        },
        'default_attributes': [
            {'name': 'Material', 'option': specs.get('material', '')},
            {'name': 'Variant', 'option': specs.get('variant', '')}
        ],
        'categories': categories,
        'manage_stock': True,
        'stock_quantity': product.get('stock_quantity', 0)
    }

    if sale_price is not None and sale_price > 0:
        product_data['sale_price'] = str(sale_price)

    # Create or update the product in WooCommerce
    create_or_update_product_in_woocommerce(product_data)

print("All products have been uploaded to WooCommerce.")
