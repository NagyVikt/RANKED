import json
from RANKED.RENDSZER.settings import INPUT_JSON_FILE, OUTPUT_JSON_FILE

# Load JSON data from a file
with open(INPUT_JSON_FILE, 'r', encoding='utf-8') as file:
    products = json.load(file)

# Add stock_quantity: 0 if it is not present
for product in products:
    if "stock_quantity" not in product:
        product["stock_quantity"] = 0

# Save the updated JSON data back to the file
with open(OUTPUT_JSON_FILE, 'w', encoding='utf-8') as file:
    json.dump(products, file, indent=4, ensure_ascii=False)

print("The file has been updated.")
