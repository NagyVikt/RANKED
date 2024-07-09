import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin
from config import api_key  # Import the API key from the config file
import re

# Base URL to scrape
base_url = 'https://www.alza.sk/notebooky/18842920.htm'

def get_html_content(url):
    try:
        response = requests.get(f'http://api.scraperapi.com?api_key={api_key}&url={url}')
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def parse_price(price_str):
    # Remove any non-digit characters except for decimal separator
    price = re.sub(r'[^\d,]', '', price_str)
    return float(price.replace(',', '.'))

def extract_product_data(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    products = []
    
    for item in soup.select('.box.browsingitem'):
        product = {}
        
        # Extract product name
        name_tag = item.select_one('.name.browsinglink')
        if name_tag:
            product['name'] = name_tag.get_text(strip=True)
        
        # Extract product link
        link_tag = item.select_one('.name.browsinglink')
        if link_tag:
            product['link'] = urljoin(base_url, link_tag['href'])
        
        # Extract product image
        img_tag = item.select_one('.box-image')
        if img_tag:
            product['image_url'] = img_tag['srcset'].split(',')[0].split(' ')[0]
        
        # Extract product description
        desc_tag = item.select_one('.Description')
        if desc_tag:
            description = desc_tag.get_text(strip=True)
            product['description'] = description
            # Extract specific details from the description
            product_details = {
                "RAM": re.search(r'RAM\s+(\d+GB)', description).group(1) if re.search(r'RAM\s+(\d+GB)', description) else None,
                "GPU": re.search(r'GPU,\s+([\w\s\d\-]+)', description).group(1) if re.search(r'GPU,\s+([\w\s\d\-]+)', description) else None,
                "SSD": re.search(r'SSD\s+(\d+GB)', description).group(1) if re.search(r'SSD\s+(\d+GB)', description) else None,
                "weight": re.search(r'hmotnosť\s+([\d,]+)\s+kg', description).group(1) if re.search(r'hmotnosť\s+([\d,]+)\s+kg', description) else None
            }
            product.update(product_details)
        
        # Extract product rating
        rating_tag = item.select_one('.star-rating-wrapper')
        if rating_tag:
            product['rating'] = 0
        
        # Extract product price
        price_tag = item.select_one('.price-box__price')
        if price_tag:
            product['price'] = parse_price(price_tag.get_text(strip=True))
        
        # Extract original price if available
        original_price_tag = item.select_one('.price-box__price-save-text')
        if original_price_tag:
            saved_amount = parse_price(original_price_tag.get_text(strip=True))
            product['original_price'] = product['price'] + saved_amount
        
        # Extract stock status
        stock_status_tag = item.select_one('.avlVal')
        if stock_status_tag:
            stock_text = stock_status_tag.get_text(strip=True)
            stock_match = re.search(r'Na sklade > (\d+)', stock_text)
            if stock_match:
                product['stock_status'] = int(stock_match.group(1))
            else:
                stock_match = re.search(r'Na sklade (\d+)', stock_text)
                if stock_match:
                    product['stock_status'] = int(stock_match.group(1))
                else:
                    product['stock_status'] = stock_text  # If it doesn't match the expected format
        
        # Extract additional details
        order_code_tag = item.select_one('.codec .code')
        if order_code_tag:
            product['order_code'] = order_code_tag.get_text(strip=True)
        
        products.append(product)
    
    return products

def main():
    products = []
    page = 1
    print(f"Fetching page {page}...")
    html_content = get_html_content(f'{base_url}#f&cst=null&cud=0&pg={page}&prod=')
    if html_content:
        page_products = extract_product_data(html_content)
        if page_products:
            products.extend(page_products)
    
    with open('alza_products.json', 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=4)
    
    print("Product data extracted and saved to 'alza_products.json'.")

if __name__ == '__main__':
    main()
