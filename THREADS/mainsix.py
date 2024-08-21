import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
from config.config import api_key

# Function to fetch HTML content using ScraperAPI with delay
def get_html_content(url):
    try:
        print(f"Fetching URL: {url}")
        payload = {
            'api_key': api_key,
            'url': url,
            'render': 'true',
            'device_type': 'desktop',
            'wait_for_selector': 'p[data-delivery-message]'
        }
        response = requests.get('https://api.scraperapi.com/', params=payload)
        response.raise_for_status()
        print("Successfully fetched the URL")
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

# Function to fetch additional details from the product page
def fetch_additional_details(product_url):
    print(f"Fetching additional details for URL: {product_url}")
    html_content = get_html_content(product_url)
    if not html_content:
        print("Failed to fetch HTML content")
        return None

    soup = BeautifulSoup(html_content, 'html.parser')
    additional_details = {}

    # Extracting stock number
    stock_tag = soup.find('p', {'data-delivery-message': True})
    if stock_tag:
        stock_match = re.search(r'(\d+)\s*db', stock_tag.text)
        if stock_match:
            additional_details['stock_quantity'] = int(stock_match.group(1))
            print(f"Extracted stock quantity: {additional_details['stock_quantity']}")
        else:
            print("Stock quantity not found in text")
    else:
        print("Stock tag not found")

    # Extracting product main description
    description_tag = soup.find('div', class_='rich-text')
    if description_tag:
        additional_details['description'] = description_tag.get_text(separator=' ').strip()
        print(f"Extracted description: {additional_details['description']}")
    else:
        print("Description not found")

    # Extracting súly
    suly_match = re.search(r'Súly:\s*([\d,]+ g)', additional_details.get('description', ''))
    if suly_match:
        additional_details['weight'] = suly_match.group(1)
        print(f"Extracted súly: {additional_details['weight']}")
    else:
        print("Súly not found in text")

    # Extracting dimensions
    dimensions = {}
    height_match = re.search(r'Magasság \(A\):\s*([\d,]+ mm)', additional_details.get('description', ''))
    width_match = re.search(r'Átmérő \(B\):\s*([\d,]+ mm)', additional_details.get('description', ''))
    if height_match:
        dimensions['height'] = height_match.group(1)
    if width_match:
        dimensions['width'] = width_match.group(1)
    
    additional_details['dimensions'] = dimensions

    # Extracting SKU and WooCommerce ID if available
    sku_match = re.search(r'SKU:\s*(\S+)', additional_details.get('description', ''))
    woo_id_match = re.search(r'WooCommerce ID:\s*(\d+)', additional_details.get('description', ''))
    if sku_match:
        additional_details['sku'] = sku_match.group(1)
    if woo_id_match:
        additional_details['woo_id'] = int(woo_id_match.group(1))

    return additional_details

# Function to update products with additional details
def update_products_with_additional_details(json_filename):
    print(f"Loading JSON file: {json_filename}")
    with open(json_filename, 'r', encoding='utf-8') as f:
        products = json.load(f)
    print(f"Loaded {len(products)} products")

    updated_products = []

    for i, product in enumerate(products):
        product_url = product.get('link')
        if product_url:
            print(f"Processing product {i+1}/{len(products)}: {product['name']}")
            additional_details = fetch_additional_details(product_url)
            if additional_details:
                product.update(additional_details)
                product['short_description'] = f"Átmérő: {product['dimensions'].get('width', '')}\nMagasság: {product['dimensions'].get('height', '')}\nSúly: {product.get('weight', '')}"
                # Add the current date and time as the updated property
                product['updated'] = datetime.now().strftime('%B %d, %Y %H:%M:%S')
                updated_products.append(product)
                print(f"Updated product: {product['name']} with additional details and timestamp")
            else:
                print(f"Failed to fetch additional details for product: {product['name']}")
            # Save updated product incrementally
            with open("emelotechnika-kampok-es-lancok-80-es-100-osztaly2.json", 'w', encoding='utf-8') as f:
                json.dump(updated_products, f, ensure_ascii=False, indent=4)
            print(f"Saved updated product {i+1} to JSON file: {json_filename}")
        else:
            print(f"No URL found for product: {product['name']}")

    print("All products have been processed and saved.")

    return updated_products

# Main script execution
if __name__ == "__main__":
    json_filename = 'emelotechnika-kampok-es-lancok-80-es-100-osztaly.json'
    updated_products = update_products_with_additional_details(json_filename)
    print(f"Updated products with additional details and saved to {json_filename}")
