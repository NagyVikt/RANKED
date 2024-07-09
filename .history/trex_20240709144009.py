import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin
from datetime import datetime
from config import api_key  # Import the API key from the config file

# Product name to search
product_name = 'Lenovo Legion Pro 5'

# Base URL to scrape
base_url = 'https://www.arukereso.hu/'

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
    search_url_with_params = f"{search_url}?st={product_name}"
    return get_html_content(search_url_with_params)

def parse_description(description):
    cpu = None
    gpu = None
    ram = None
    ram_type = None
    ssd = None

    description_lines = description.split(' ')
    for i, part in enumerate(description_lines):
        if part.lower() == 'típusa':
            cpu = ' '.join(description_lines[i+1:i+3])
        elif part.lower() == 'mérete':
            if 'GB' in description_lines[i+1] or 'MB' in description_lines[i+1]:
                ram = description_lines[i+1]
            elif 'Cache' in description_lines[i+1]:
                continue  # Skip Cache size
        elif part.lower() == 'típusa' and 'memória' in description_lines[i-1].lower():
            ram_type = description_lines[i+1]
        elif part.lower() == 'ssd':
            ssd = description_lines[i+1]
        elif part.lower() == 'gpu':
            gpu = ' '.join(description_lines[i+1:i+3])

    return cpu, gpu, ram, ram_type, ssd

def parse_search_results(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    product_list = []

    product_divs = soup.find_all('div', class_='product-box clearfix')
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    for product_div in product_divs:
        product = {}
        product_link_tag = product_div.find('a', class_='image')
        if product_link_tag:
            product_link = product_link_tag.get('href')
            if product_link:
                product['link'] = urljoin(base_url, product_link)
            product['name'] = product_link_tag.get('title', 'No title available')
        
        img_tag = product_div.find('img')
        if img_tag and 'src' in img_tag.attrs:
            product['image'] = img_tag['src']
        else:
            product['image'] = 'No image available'

        price_tag = product_div.find('div', class_='price')
        if price_tag:
            product['price'] = price_tag.text.strip()
        else:
            product['price'] = 'No price available'

        offer_num_tag = product_div.find('span', class_='offer-num')
        if offer_num_tag:
            product['offers'] = offer_num_tag.text.strip()
        else:
            product['offers'] = 'No offers available'

        description_tag = product_div.find('div', class_='description clearfix hidden-xs')
        if description_tag:
            description = description_tag.get_text(separator=' ', strip=True)
            cpu, gpu, ram, ram_type, ssd = parse_description(description)
            product['description'] = {
                'CPU': cpu,
                'GPU': gpu,
                'RAM': ram,
                'RAM Type': ram_type,
                'SSD': ssd,
                'Full Description': description
            }
        else:
            product['description'] = 'No description available'

        product['timestamp'] = current_time

        product_list.append(product)

    return product_list

def main():
    # Search for the product
    search_html = search_product(product_name)
    if search_html:
        # Parse search results
        products = parse_search_results(search_html)
        if products:
            # Save the products as JSON to a file
            with open('products.json', 'w', encoding='utf-8') as f:
                json.dump(products, f, indent=4, ensure_ascii=False)
            print("Products have been saved to 'products.json'.")
        else:
            print("No products found.")
    else:
        print("Failed to retrieve search results.")

if __name__ == "__main__":
    main()
