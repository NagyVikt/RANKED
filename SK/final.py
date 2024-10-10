import json
import requests
import os
from urllib.parse import urljoin
import base64

# WooCommerce API credentials
username = 'Deadpool'
password = 'Karategi123'
wp_base_url = 'https://kdtech.sk/wp-json/'
wc_base_url = 'https://kdtech.sk/wp-json/wc/v3/'

# Encode credentials for HTTP Basic Authentication
auth_string = f'{username}:{password}'
auth_header = {
    'Authorization': 'Basic ' + base64.b64encode(auth_string.encode()).decode(),
    'Content-Type': 'application/json'
}

# Function to check if a category exists by slug
def get_category_by_slug(slug):
    url = urljoin(wc_base_url, 'products/categories')
    params = {'slug': slug}
    response = requests.get(url, headers=auth_header, params=params)
    if response.status_code == 200:
        categories = response.json()
        if categories:
            return categories[0]  # Return the first matching category
    else:
        print(f"Failed to retrieve category '{slug}'. Response: {response.text}")
    return None

# Function to create a category
def create_category(name, slug, parent_id=None):
    url = urljoin(wc_base_url, 'products/categories')
    data = {
        'name': name,
        'slug': slug,
    }
    if parent_id:
        data['parent'] = parent_id
    response = requests.post(url, headers=auth_header, json=data)
    if response.status_code == 201:
        category = response.json()
        print(f"Category '{name}' created with ID {category['id']}.")
        return category
    else:
        print(f"Failed to create category '{name}'. Response: {response.text}")
        return None

# Function to ensure all categories exist in WooCommerce and build ID mapping
def ensure_categories(categories_list):
    category_id_mapping = {}  # Mapping from original ID to WooCommerce ID

    for category in categories_list:
        original_id = category['id']
        name = category['name']
        slug = category['slug']

        # Check if category exists
        existing_category = get_category_by_slug(slug)
        if existing_category:
            wc_category_id = existing_category['id']
            print(f"Category '{name}' already exists with ID {wc_category_id}.")
        else:
            # Create category
            new_category = create_category(name, slug)
            if new_category:
                wc_category_id = new_category['id']
            else:
                print(f"Failed to create category '{name}'. Skipping.")
                continue  # Skip to the next category
        # Map original ID to WooCommerce ID
        category_id_mapping[original_id] = wc_category_id

    return category_id_mapping

# Function to update products with correct category IDs
def update_products_with_categories(products, category_id_mapping):
    for product in products:
        product_id = product.get('id')
        if not product_id:
            print(f"Product '{product.get('name', 'Unnamed')}' has no ID. Skipping.")
            continue  # Skip if product ID is missing

        # Map original category IDs to WooCommerce category IDs
        original_categories = product.get('categories', [])
        wc_categories = []
        for cat in original_categories:
            original_cat_id = cat['id']
            wc_cat_id = category_id_mapping.get(original_cat_id)
            if wc_cat_id:
                wc_categories.append({'id': wc_cat_id})
            else:
                print(f"No mapping found for category ID {original_cat_id}. Skipping category.")

        if not wc_categories:
            print(f"No valid categories for product '{product.get('name', 'Unnamed')}'. Skipping update.")
            continue

        # Prepare data for updating the product
        product_data = {
            'categories': wc_categories
        }

        # Update the product in WooCommerce
        update_product_in_woocommerce(product_id, product_data)

# Function to update a product in WooCommerce
def update_product_in_woocommerce(product_id, product_data):
    url = urljoin(wc_base_url, f"products/{product_id}")
    response = requests.put(url, headers=auth_header, json=product_data)
    if response.status_code == 200:
        print(f"Product ID {product_id} updated successfully.")
        return response.json()
    else:
        print(f"Failed to update product ID {product_id}. Response: {response.text}")
        return None

def main():
    # Load the updated products JSON file
    with open('final.json', 'r', encoding='utf-8') as f:
        updated_products = json.load(f)

    # Collect all categories from updated_products
    all_categories = []
    category_ids_seen = set()
    for product in updated_products:
        for category in product.get('categories', []):
            if category['id'] not in category_ids_seen:
                all_categories.append(category)
                category_ids_seen.add(category['id'])

    # Ensure all categories exist in WooCommerce and get the mapping
    category_id_mapping = ensure_categories(all_categories)

    # Update products with correct WooCommerce category IDs
    update_products_with_categories(updated_products, category_id_mapping)

if __name__ == '__main__':
    main()
