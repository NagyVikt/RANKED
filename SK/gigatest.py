import json
import requests
import base64
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import re
from config.config import api_key

# WooCommerce API credentials
username = 'Deadpool'
password = 'Karategi123'
wp_base_url = 'https://kdtech.sk/wp-json/'
wc_base_url = 'https://kdtech.sk/wp-json/wc/v3/'

# ScraperAPI configuration

# Encode credentials for HTTP Basic Authentication
auth_string = f'{username}:{password}'
auth_header = {
    'Authorization': 'Basic ' + base64.b64encode(auth_string.encode()).decode()
}

# Function to get HTML content using ScraperAPI
def get_html_content(url):
    try:
        print(f"Fetching URL: {url}")
        
        # Base payload
        payload = {
            'api_key': api_key,
            'url': url,
            'device_type': 'desktop'
        }
        
        response = requests.get('https://api.scraperapi.com/', params=payload)
        response.raise_for_status()  # Raise an error for failed requests
        print("Successfully fetched the URL")
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
                specs['length'] = value.replace('cm', '').strip()
            elif 'Výška' in label:
                specs['height'] = value.replace('mm', '').strip()
            elif 'Váha' in label or 'Hmotnosť' in label:
                specs['weight'] = value.replace('kg', '').strip()
            elif 'Materiál' in label:
                specs['material'] = value.strip()
            elif 'Variant' in label:
                specs['variant'] = value.strip()
                
    return specs

# Function to scrape product description and short description
def scrape_descriptions(soup):
    description = ""
    short_description = ""

    # Find the product title (h2 tag) for the short description
    title_tag = soup.find('h2')
    if title_tag:
        short_description = title_tag.get_text(strip=True)

    # Find the full description inside the relevant div
    description_tag = soup.find('div', class_='rich-text w-8/12 max-sm:w-full')
    if description_tag:
        paragraphs = description_tag.find_all('p')
        description_texts = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]
        description = "\n".join(description_texts)

    # If no short description, use the first 150 characters of the description
    if not short_description:
        short_description = description[:150] + "..."

    return description, short_description

# Function to fetch product page and parse descriptions and specifications
def fetch_image_prices_specs_desc(product_url):
    html_content = get_html_content(product_url)
    
    if not html_content:
        return None, None, None
    
    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')

    # Fetch the descriptions
    description, short_description = scrape_descriptions(soup)

    # Fetch the specifications
    specifications = scrape_product_specifications(soup)

    return description, short_description, specifications

# Test it with a product URL
product_url = "https://www.svx.sk/domacnost-a-drogeria-bezpecnost-dietata/flexibilny-drziak-pod-dvere-38x128x36-mm_20855/"
description, short_description, specifications = fetch_image_prices_specs_desc(product_url)

print(f"Description: {description}")
print(f"Short Description: {short_description}")
print(f"Specifications: {specifications}")
