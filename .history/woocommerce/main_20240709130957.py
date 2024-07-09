import requests
import json

# WooCommerce REST API credentials
consumer_key = 'ck_a3cce15b0954b01a6093a4273fa403f43bddd1d5'
consumer_secret = 'cs_215e4e6f4bfb6563609aeba59e91ed7905812c86'
store_url = 'https://itrex.hu/'  # Replace with your WooCommerce store URL

def fetch_all_items(url, auth):
    page = 1
    all_items = []

    while True:
        response = requests.get(f"{url}?per_page=100&page={page}", auth=auth)
        if response.status_code != 200:
            print(f"Failed to fetch items on page {page}. Status Code: {response.status_code}")
            break

        items = response.json()
        if not items:
            break  # Exit loop if no more items

        all_items.extend(items)
        page += 1

    return all_items


# Endpoint for getting product categories
endpoint = '/wp-json/wc/v3/products/categories'
url = f"{store_url}{endpoint}"

# Fetch all categories
categories = fetch_all_items(url, (consumer_key, consumer_secret))


# Save all categories to a JSON file
with open('../JSON/woocommerce_categories.json', 'w') as file:
    json.dump(categories, file, indent=4)

# Extract 'name' and 'slug' for each item and save to a new JSON file
extracted_data = [{"name": item["name"], "slug": item["slug"]} for item in categories]
with open('../JSON/categories-with-slugs.json', 'w') as outfile:
    json.dump(extracted_data, outfile, indent=4)


# Extract unique category names
category_names = {item['name'] for item in extracted_data}

# Prepare the data in the desired format
result = {
    "categories": list(category_names)
}

# Save the result to a new JSON file
with open('../JSON/categories.json', 'w') as file:
    json.dump(result, file, indent=2)



print("Filtered categories have been saved to 'categories-filtered.json'.")

# Fetch all products
products_url = f"{store_url}/wp-json/wc/v3/products"
products = fetch_all_items(products_url, (consumer_key, consumer_secret))

# Save all products to a JSON file
with open('../JSON/woocommerce_products.json', 'w') as file:
    json.dump(products, file, indent=4)


# Define a new list to hold the simplified product information
simplified_products = []

# Iterate over the original product list
for product in products:
    # Extract the relevant information and add it to the simplified_products list
    simplified_product = {
        "id": product["id"],
        "name": product["name"],
        "sku": product.get("sku", ""),  # Using .get() to avoid KeyError if the key doesn't exist
        "price": product["price"],
        "type": product["type"],
        "regular_price": product["regular_price"],
        "sale_price": product["sale_price"],
        "stock_status": product["stock_status"],
        "on_sale": product["on_sale"],
        "stock_quantity": product.get("stock_quantity", 0),  # Assuming stock quantity might not be present for all products
        "description": product.get("description", ""),  # Include the description, with a default of an empty string if not present
        "short_description": product.get("short_description",""),
        "total_sales": product.get("total_sales", 0),
        "tags": product.get("tags", ""),
        "categories": product.get("categories","")
    }
    simplified_products.append(simplified_product)

# Convert the simplified product list to JSON and save it to a file
with open('../JSON/simplified_products.json', 'w') as file:
    json.dump(simplified_products, file, indent=4)

print("All categories and products have been saved to their respective JSON files.")