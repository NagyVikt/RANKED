import json
import random

# Load the JSON file
with open('magnesek.json', 'r', encoding='utf-8') as file:
    products = json.load(file)

# Function to generate a new Woo ID
def generate_woo_id():
    return random.randint(10000, 99999)

# Function to generate a new SKU
def generate_sku():
    return f"SKU-{random.randint(100000, 999999)}"

# Function to extract dimensions from attributes
def extract_dimensions(attributes):
    dimensions = {
        "length": "",
        "width": "",
        "height": ""
    }
    for attr in attributes:
        if 'Átmérő' in attr:
            dimensions["width"] = attr.split(":")[1].strip()
        elif 'Magasság' in attr:
            dimensions["height"] = attr.split(":")[1].strip()
        elif 'Hosszúság' in attr:
            dimensions["length"] = attr.split(":")[1].strip()
        elif 'Szélesség' in attr:
            dimensions["width"] = attr.split(":")[1].strip()
    return dimensions

# Update each product
for product in products:
    product['woo_id'] = generate_woo_id()
    product['sku'] = generate_sku()
    product['weight'] = product.pop('suly', '')
    product['dimensions'] = extract_dimensions(product.pop('attributes', []))
    product['short_description'] = "\n".join([
        f"Átmérő (mm): {product['dimensions']['width']}",
        f"Magasság (mm): {product['dimensions']['height']}",
        f"Súly: {product['weight']}"
    ])

# Save the updated JSON file
with open('magnesek_updated.json', 'w', encoding='utf-8') as file:
    json.dump(products, file, ensure_ascii=False, indent=4)

print("Updated JSON file has been saved as 'magnesek_updated.json'")
