import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin
import re
from config import api_key
# Replace with your Scraper API key and desired category
api_key = 'YOUR_API_KEY'
category = 'notebook-c3100'
product_name = 'Lenovo Legion Pro 5'

# Base URL to scrape
base_url = f'https://www.arukereso.hu/{category}/'

def get_html_content(url):
    try:
        response = requests.get(f'http://api.scraperapi.com?api_key={api_key}&url={url}')
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def search_product(product_name):
    search_url = 'https://www.arukereso.hu/CategorySearch.php'
    params = {'st': product_name}
    response = requests.get(f'http://api.scraperapi.com?api_key={api_key}&url={search_url}', params=params)
    if response.status_code == 200:
        return response.text
    else:
        print(f"Error searching for product: {response.status_code}")
        return None

def parse_search_results(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    product_list = []

    product_divs = soup.find_all('div', class_='product-box clearfix')
    for product_div in product_divs:
        product = {}
        product_link = product_div.find('a', class_='image')['href']
        product['link'] = urljoin(base_url, product_link)
        product['name'] = product_div.find('a', class_='image')['title']
        product['image'] = product_div.find('img')['src']
        product['price'] = product_div.find('div', class_='price').text.strip()
        product['offers'] = product_div.find('span', class_='offer-num').text.strip()
        
        description = product_div.find('div', class_='description clearfix hidden-xs')
        if description:
            product['description'] = description.get_text(separator=' ', strip=True)
        else:
            product['description'] = None

        product_list.append(product)

    return product_list

def main():
    # Search for the product
    search_html = search_product(product_name)
    if search_html:
        # Parse search results
        products = parse_search_results(search_html)
        if products:
            # Output the products as JSON
            print(json.dumps(products, indent=4, ensure_ascii=False))
        else:
            print("No products found.")
    else:
        print("Failed to retrieve search results.")

if __name__ == "__main__":
    main()
