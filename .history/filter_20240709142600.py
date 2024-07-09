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

# Function to extract attributes from the description
def extract_attributes(description):
    attributes = {}
    # Extract CPU type
    cpu_match = re.search(r'Processzor típusa :\s*([A-Za-z0-9\s]+)', description)
    if cpu_match:
        attributes['cpu'] = cpu_match.group(1).strip()

    # Extract CPU clock speed
    clock_match = re.search(r'Processzor órajel :\s*([\d\.]+ GHz)', description)
    if clock_match:
        attributes['clock'] = clock_match.group(1).strip()

    # Extract Cache size
    cache_match = re.search(r'Cache mérete :\s*(\d+ MB)', description)
    if cache_match:
        attributes['cache'] = cache_match.group(1).strip()

    # Extract RAM size
    ram_match = re.search(r'Memória mérete :\s*(\d+ GB)', description)
    if ram_match:
        attributes['ram'] = ram_match.group(1).strip()

    # Extract RAM type
    ram_type_match = re.search(r'Memória típusa :\s*(DDR\d)', description)
    if ram_type_match:
        attributes['ram_type'] = ram_type_match.group(1).strip()

    return attributes

# Group products by their attributes
grouped_laptops = {}
for laptop in laptops:
    attributes = extract_attributes(laptop['description'])
    attr_key = f"{attributes.get('cpu', 'Unknown')} | {attributes.get('clock', 'Unknown')} | {attributes.get('cache', 'Unknown')} | {attributes.get('ram', 'Unknown')}GB {attributes.get('ram_type', 'Unknown')}"
    if attr_key not in grouped_laptops:
        grouped_laptops[attr_key] = []
    grouped_laptops[attr_key].append(laptop)

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
