
import json
import matplotlib.pyplot as plt
import re

# Load the data from the JSON file
with open('products.json', 'r', encoding='utf-8') as f:
    products = json.load(f)

# Function to filter out non-laptop products
def is_laptop(product):
    if "Notebook" in product['name'] or "laptop" in product['name']:
        return True
    return False

# Filter the list of products to include only laptops
laptops = [product for product in products if is_laptop(product)]

# Function to normalize product names for grouping
def normalize_name(name):
    name = re.sub(r'\s+', ' ', name)  # Remove extra spaces
    name = re.sub(r'\s*\([^)]*\)', '', name)  # Remove text in parentheses
    name = name.strip().lower()
    return name

# Group products by their normalized names
grouped_laptops = {}
for laptop in laptops:
    normalized_name = normalize_name(laptop['name'])
    if normalized_name not in grouped_laptops:
        grouped_laptops[normalized_name] = []
    grouped_laptops[normalized_name].append(laptop)

# Function to extract price range from price string
def extract_price(price_str):
    prices = re.findall(r'\d+', price_str.replace(' ', ''))
    if prices:
        return int(prices[0])
    return None

# Create a price range graph
for group_name, group_laptops in grouped_laptops.items():
    prices = [extract_price(laptop['price']) for laptop in group_laptops if extract_price(laptop['price']) is not None]
    if not prices:
        continue

    plt.figure()
    plt.hist(prices, bins=range(min(prices), max(prices) + 10000, 10000), edgecolor='black')
    plt.title(f'Price Range for {group_name}')
    plt.xlabel('Price (Ft)')
    plt.ylabel('Number of Offers')
    plt.grid(True)
    plt.show()

# Save the grouped products to a new JSON file
with open('grouped_products.json', 'w', encoding='utf-8') as f:
    json.dump(grouped_laptops, f, indent=4, ensure_ascii=False)

print("Grouped products have been saved to 'grouped_products.json'.")
