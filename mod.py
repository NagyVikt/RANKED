import json
import re

# Load the JSON data from a file
with open('magnesek_updated.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

# Function to update the short_description and weight
def update_product(product):
    # Extracting values from the description
    description = product.get('description', '')
    print(f"Processing product: {product.get('name')}")
    
    # Patterns for extracting dimensions and weight
    dimensions_pattern = re.compile(r"Mérete:\s*(\d+[,.]?\d*)x(\d+[,.]?\d*)x(\d+[,.]?\d*)\s*mm|Mérete:\s*(\d+[,.]?\d*)x(\d+[,.]?\d*)\s*mm|Hosszúság\s*\(A\):\s*(\d+[,.]?\d*)\s*(mm|m)\s*Szélesség\s*\(B\):\s*(\d+[,.]?\d*)\s*(mm|m)")
    weight_pattern = re.compile(r"Súly:\s*(\d+[,.]?\d*)\s*g")
    
    dimensions_match = dimensions_pattern.search(description)
    weight_match = weight_pattern.search(description)
    
    length = width = height = diameter = None
    
    if dimensions_match:
        if dimensions_match.group(1) and dimensions_match.group(2) and dimensions_match.group(3):
            length = dimensions_match.group(1).replace(',', '.')
            width = dimensions_match.group(2).replace(',', '.')
            height = dimensions_match.group(3).replace(',', '.')
            print(f"Extracted dimensions: {length}x{width}x{height} mm")
        elif dimensions_match.group(4) and dimensions_match.group(5):
            diameter = dimensions_match.group(4).replace(',', '.')
            height = dimensions_match.group(5).replace(',', '.')
            print(f"Extracted dimensions: {diameter} mm diameter, {height} mm height")
        elif dimensions_match.group(6) and dimensions_match.group(7):
            length = dimensions_match.group(6).replace(',', '.')
            width = dimensions_match.group(8).replace(',', '.')
            length_unit = dimensions_match.group(7)
            width_unit = dimensions_match.group(9)
            print(f"Extracted dimensions: {length} {length_unit} x {width} {width_unit}")
    else:
        print("Dimensions not found.")
    
    if weight_match:
        weight = weight_match.group(1).replace(',', '.')
        print(f"Extracted weight: {weight} g")
    else:
        print("Weight not found.")
    
    # Update dimensions and weight
    if length and width and height:
        product['dimensions'] = {
            "length": f"{length} mm",
            "width": f"{width} mm",
            "height": f"{height} mm"
        }
    elif diameter and height:
        product['dimensions'] = {
            "length": "",
            "width": f"{diameter} mm",
            "height": f"{height} mm"
        }
    elif length and width:
        product['dimensions'] = {
            "length": f"{length} {length_unit}",
            "width": f"{width} {width_unit}",
            "height": ""
        }
    
    if weight_match:
        product['weight'] = f"{weight} g"
    
    # Update short_description
    if length and width and height and weight:
        product['short_description'] = f"Hosszúság: {length} mm\nSzélesség: {width} mm\nMagasság: {height} mm\nSúly: {weight} g"
    elif diameter and height and weight:
        product['short_description'] = f"Átmérő: {diameter} mm\nMagasság: {height} mm\nSúly: {weight} g"
    elif length and width and weight:
        product['short_description'] = f"Hosszúság: {length} {length_unit}\nSzélesség: {width} {width_unit}\nSúly: {weight} g"
    elif weight:
        product['short_description'] = f"Súly: {weight} g"
    elif length and width and height:
        product['short_description'] = f"Hosszúság: {length} mm\nSzélesség: {width} mm\nMagasság: {height} mm"
    else:
        print(f"Skipping update for product: {product.get('name')} due to missing information.")
        
    return product

# Apply the update to each product and save the updated JSON data to a file continuously
for product in data:
    updated_product = update_product(product)
    
    # Save the updated product to the JSON file
    with open('magnesek2.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

print("Products updated successfully!")
