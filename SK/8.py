import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
from config.config import api_key
import random

# Load the new category configuration
categories = [
    {"id": 98, "name": "Domácnosť a drogéria", "slug": "domacnost-a-drogeria"},
    {"id": 94, "name": "Elektroinštalačný materiál", "slug": "elektroinstalacny-material"},
    {"id": 86, "name": "Laná, reťaze a sťahovacie pásky", "slug": "lana-retaze-a-stahovacie-pasky"},
    {"id": 85, "name": "Lanové príslušenstvo a nerezový program", "slug": "lanove-prislusenstvo-a-nerezovy-program"},
    {"id": 99, "name": "Ložiská, guferá, klinové remene a príslušenstvo", "slug": "loziska-gufera-klinove-remene-a-prislusenstvo"},
    {"id": 101, "name": "Magnety", "slug": "magnety"},
    {"id": 97, "name": "Náradie", "slug": "naradie"},
    {"id": 92, "name": "Ochranné pracovné prostriedky Delta plus", "slug": "ochranne-pracovne-prostriedky-delta-plus"},
    {"id": 91, "name": "Pätky, uholníky a kovania", "slug": "patky-uholniky-a-kovania"},
    {"id": 100, "name": "Pletivá", "slug": "pletiva"},
    {"id": 93, "name": "Predlžovacie káble a svietidlá Brennenstuhl", "slug": "predlzovacie-kable-a-svietidla-brennenstuhl"},
    {"id": 102, "name": "Rebríky ALVE", "slug": "rebriky-alve"},
    {"id": 88, "name": "Reťazové a textilné úväzky", "slug": "retazove-a-textilne-uvazky"},
    {"id": 95, "name": "Spojovací a kotviaci materiál", "slug": "spojovaci-a-kotviaci-material"},
    {"id": 96, "name": "Stavebná chémia", "slug": "stavbena-chemia"},
    {"id": 89, "name": "Upínacie pásy - gurtne a príslušenstvo", "slug": "upinacie-pasy-gurtne-a-prislusenstvo"},
    {"id": 90, "name": "Zdvíhacia a manipulačná technika YALE-PFAFF", "slug": "zdvihacia-a-manipulacna-technika-yale-pfaff"},
    {"id": 87, "name": "Zdvíhacia technika, háky a reťaze tr 80 a tr 100", "slug": "zdvihacia-technika-haky-a-retaze-tr-80-a-tr-100"}
]

category_id = 88
total_pages = 58  # This is the variable you can redefine each run

def get_html_content(url, wait_for_selector=None):
    try:
        print(f"Fetching URL: {url}")
        
        # Base payload
        payload = {
            'api_key': api_key,
            'url': url,
            'render': 'true',
            'device_type': 'desktop'
        }
        
        # Redefine payload if wait_for_selector is provided
        if wait_for_selector:
            payload = {
                'api_key': api_key,
                'url': url,
                'render': 'true',
                'device_type': 'desktop',
                'wait_for_selector': wait_for_selector
            }
        
        response = requests.get('https://api.scraperapi.com/', params=payload)
        response.raise_for_status()
        print("Successfully fetched the URL")
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None


def generate_sku(category_id):
    return f"SKU{category_id}{random.randint(10000, 99999)}"

# Function to extract product links and basic info from the category page
def extract_product_info_from_category_page(category_url):
    html_content = get_html_content(category_url)
    if not html_content:
        print(f"Failed to fetch content from {category_url}")
        return []

    soup = BeautifulSoup(html_content, 'html.parser')
    product_infos = []

    # Select the div containing the product links
    for product_card in soup.select('div.product-card-main'):
        link_tag = product_card.find('a', href=True)
        if link_tag:
            product_url = f"https://www.svx.sk{link_tag['href']}"  # Adjust domain if needed
            product_name = link_tag.get_text().strip()

            # Extract the stock quantity from the category page
            stock_tag = product_card.find('div', {'data-stock-state-class': True})
            stock_quantity = 0
            if stock_tag:
                stock_match = re.search(r'(\d+)\s*ks', stock_tag.text)
                if stock_match:
                    stock_quantity = int(stock_match.group(1))

            # Extract the price from the category page
            price_tag = product_card.find('div', {'data-config-product-price-primary': True})
            price = price_tag.get_text().strip() if price_tag else ""

            product_infos.append({
                'name': product_name,
                'link': product_url,
                'price': price,
                'stock_quantity': stock_quantity
            })

    print(f"Extracted {len(product_infos)} products from the category page")
    return product_infos

# Function to fetch additional details from the product page
def fetch_additional_details(product_info):
    html_content = get_html_content(product_info['link'], wait_for_selector='p[data-delivery-message]')
    if not html_content:
        return None

    soup = BeautifulSoup(html_content, 'html.parser')
    additional_details = {}

    # Extracting product name (in case it wasn't extracted correctly from the category page)
    name_tag = soup.find('h1', {'data-testid': 'product-title'})
    if name_tag:
        additional_details['name'] = name_tag.get_text().strip()



    # Extracting product attributes
    attributes = []
    attribute_tags = soup.find_all('div', class_='attribute-class')  # Update this selector as needed
    for attribute in attribute_tags:
        attributes.append(attribute.get_text().strip())
    additional_details['attributes'] = attributes

    # Extracting product image
    image_tag = soup.find('img', {'class': 'product-image-class'})  # Update this selector
    if image_tag:
        additional_details['image'] = image_tag['src']

    # Extracting product description
    description_tag = soup.find('div', {'class': 'description-class'})  # Update this selector
    if description_tag:
        additional_details['description'] = description_tag.get_text(separator=' ').strip()

    # Extracting stock quantity
    stock_tag = soup.find('p', {'data-delivery-message': True})
    if stock_tag:
        stock_match = re.search(r'(\d+)\s*ks', stock_tag.text)
        if stock_match:
            additional_details['stock_quantity'] = int(stock_match.group(1))
    


    additional_details['sku'] = generate_sku(category_id)




  # Extracting regular and sale price
    regular_price_tag = soup.find('div', {'data-config-product-price-primary': True})
    sale_price_tag = soup.find('div', {'data-config-product-price-secondary': True})

    if regular_price_tag:
        regular_price = float(re.sub(r'[^\d,]', '', regular_price_tag.get_text().strip()).replace(',', '.'))
        additional_details['regular_price'] = regular_price
        additional_details['price'] = f"{regular_price}"  # Setting the price as well

    # Handling sale price if it exists
    sale_price = None
    discount_tag = soup.find('span', class_='text-brand')  # Look for discount class
    if discount_tag:
        sale_price_tag = soup.find('div', {'data-config-product-price-primary': True})
        if sale_price_tag:
            sale_price = float(re.sub(r'[^\d,]', '', sale_price_tag.get_text().strip()).replace(',', '.'))
            additional_details['sale_price'] = sale_price
            additional_details['price'] = f"{sale_price} €"  # Overwrite the price with the sale price
    else:
        additional_details['sale_price'] = 0  # No sale price


    # Dimensions placeholder
    additional_details['dimensions'] = {}

    # Category details (extracted from the category page URL)
    additional_details['categories'] = [{
        "id": category_id,  # Update this ID to match the category ID if known
        "name": "Reťazové a textilné úväzky",
        "slug": "retazove-a-textilne-uvazky"
    }]

    # Update the product info with additional details
    product_info.update(additional_details)
    return product_info

# Function to save each product individually after fetching its details
def save_product_to_json(product_info):
    with open(output_json_filename, 'a', encoding='utf-8') as f:
        json.dump(product_info, f, ensure_ascii=False, indent=4)
        f.write(',\n')  # Add a comma and newline for separation between products
    print(f"Saved product: {product_info['name']} to JSON file")
# Function to load existing products from the JSON file
def load_existing_products(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            existing_products = json.load(f)
            existing_urls = {product['link'] for product in existing_products}
            return existing_urls
    except FileNotFoundError:
        return set()  # Return an empty set if the file doesn't exist

# Main script execution
if __name__ == "__main__":

    base_category_url = 'https://www.svx.sk/retazove-a-textilne-uvazky/'  # Base URL of the category
    output_json_filename = 'retazove-a-textilne-uvazky_new.json'
    existing_product_urls = load_existing_products('retazove-a-textilne-uvazky.json')

    # Create or clear the JSON file before starting the scraping process
    with open(output_json_filename, 'w', encoding='utf-8') as f:
        f.write('[\n')  # Start JSON array

    for page_number in range(1, total_pages + 1):
        category_url = f"{base_category_url}?p={page_number}"
        print(f"Processing page {page_number} of {total_pages}: {category_url}")

        product_infos = extract_product_info_from_category_page(category_url)

        for product_info in product_infos:
            if product_info['link'] in existing_product_urls:
                print(f"Skipping existing product: {product_info['name']}")
                continue

            print(f"New product found: {product_info['name']}")
            full_product_info = fetch_additional_details(product_info)
            if full_product_info:
                save_product_to_json(full_product_info)
    # Close the JSON array
    with open(output_json_filename, 'a', encoding='utf-8') as f:
        f.write(']')  # End JSON array

    print(f"Scraping completed and data saved to {output_json_filename}")
