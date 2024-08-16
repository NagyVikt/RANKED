import json
import requests
import base64
from urllib.parse import urljoin

# WooCommerce API credentials
username = 'Deadpool'
password = 'Karategi123'
wc_base_url = 'https://kdtech.hu/wp-json/wc/v3/'

# Encode credentials for HTTP Basic Authentication
auth_string = f'{username}:{password}'
auth_header = {
    'Authorization': 'Basic ' + base64.b64encode(auth_string.encode()).decode()
}

# Function to get all categories from WooCommerce
def get_all_categories():
    categories = []
    page = 1
    while True:
        url = urljoin(wc_base_url, 'products/categories')
        params = {'per_page': 100, 'page': page}
        response = requests.get(url, headers=auth_header, params=params)
        if response.status_code == 200:
            page_categories = response.json()
            if not page_categories:
                break
            categories.extend(page_categories)
            page += 1
        else:
            print(f"Failed to fetch categories. Response: {response.text}")
            break
    return categories

# Fetch categories
categories = get_all_categories()

# Extract category ID and name
categories_data = [{'id': category['id'], 'name': category['name']} for category in categories]

# Save to JSON file
with open('categories.json', 'w', encoding='utf-8') as file:
    json.dump(categories_data, file, ensure_ascii=False, indent=4)

print("Categories have been saved to 'categories.json'")
