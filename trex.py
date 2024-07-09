import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin

# ScraperAPI key
api_key = '6667a4085b3eaf440230e75290783fa5'

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
        
        # Extract product price
        price_tag = item.select_one('.price-box__price')
        if price_tag:
            product['price'] = price_tag.get_text(strip=True)
        
        # Extract product rating
        rating_tag = item.select_one('.star-rating-wrapper')
        if rating_tag:
            product['rating'] = rating_tag['data-rating']
        
        # Extract product reviews count
        reviews_count_tag = item.select_one('.star-rating-block__count')
        if reviews_count_tag:
            product['reviews_count'] = reviews_count_tag.get_text(strip=True)
        
        products.append(product)
    
    return products

def main():
    products = []
    page = 1
    while True:
        print(f"Fetching page {page}...")
        html_content = get_html_content(f'{base_url}#f&cst=null&cud=0&pg={page}&prod=')
        if not html_content:
            break
        
        page_products = extract_product_data(html_content)
        if not page_products:
            break
        
        products.extend(page_products)
        page += 1
    
    with open('alza_products.json', 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=4)
    
    print("Product data extracted and saved to 'alza_products.json'.")

if __name__ == '__main__':
    main()
