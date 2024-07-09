import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin
from config import api_key  # Import the API key from the config file

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
            product['description'] = desc_tag.get_text(strip=True)
        
        # Extract product rating
        rating_tag = item.select_one('.star-rating-wrapper')
        if rating_tag:
            product['rating'] = rating_tag.get('data-rating')
        
        # Extract product reviews count
        reviews_count_tag = item.select_one('.star-rating-block__count')
        if reviews_count_tag:
            product['reviews_count'] = reviews_count_tag.get_text(strip=True)
        
        # Extract product price
        price_tag = item.select_one('.price-box__price')
        if price_tag:
            product['price'] = price_tag.get_text(strip=True)
        
        # Extract original price if available
        original_price_tag = item.select_one('.price-box__price-save-text')
        if original_price_tag:
            product['original_price'] = original_price_tag.get_text(strip=True)
        
        # Extract stock status
        stock_status_tag = item.select_one('.avlVal')
        if stock_status_tag:
            product['stock_status'] = stock_status_tag.get_text(strip=True)
        
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
