import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin
from datetime import datetime
from openai import OpenAI
import os

# Load the API key from the environment variable
openai_api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=openai_api_key)
# Check if the API key is loaded properly
if not openai_api_key:
    raise ValueError("OpenAI API key not found in environment variables")

# Initialize the OpenAI API

# Product name to search
product_name = 'Lenovo Legion Pro 5'

# Base URL to scrape
base_url = 'https://www.arukereso.hu/'

def get_html_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def search_product(product_name):
    search_url = 'https://www.arukereso.hu/CategorySearch.php'
    search_url_with_params = f"{search_url}?st={product_name}"
    return get_html_content(search_url_with_params)

def parse_description_with_gpt(description):
    prompt = (
        f"Extract the following details from this description:\n"
        f"Description: {description}\n"
        f"1. CPU\n"
        f"2. GPU\n"
        f"3. RAM size\n"
        f"4. RAM type\n"
        f"5. SSD size\n\n"
        f"Provide the details in a JSON format with keys 'CPU', 'GPU', 'RAM', 'RAM Type', 'SSD'."
    )

    try:
        response = client.chat.completions.create(model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts hardware details from descriptions."},
                {"role": "user", "content": prompt}
            ])
        
        details = response.choices[0].message.content
        print(f"GPT response: {details}")  # Debugging output
        return json.loads(details)
    except Exception as e:
        print(f"Error parsing description with GPT: {e}")
        return {}

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
            details = parse_description_with_gpt(description)
            product['description'] = {
                'CPU': details.get('CPU', 'Not available'),
                'GPU': details.get('GPU', 'Not available'),
                'RAM': details.get('RAM', 'Not available'),
                'RAM Type': details.get('RAM Type', 'Not available'),
                'SSD': details.get('SSD', 'Not available'),
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
