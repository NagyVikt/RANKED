import os
import json
from datetime import datetime

# Define the directory where the JSON files are located
MINTAK_DIR = 'MINTAK'

# Function to load JSON data from a file
def load_json_data(json_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

# Function to save JSON data to a file
def save_json_data(json_file, data):
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Function to add an "updated_at" property to each object in a JSON file
def add_update_property(json_file):
    print(f"Processing file: {json_file}")
    products = load_json_data(json_file)
    current_time = datetime.now().strftime('%B %d, %Y %H:%M:%S')

    for product in products:
        product['updated_at'] = current_time
    
    save_json_data(json_file, products)
    print(f"Updated file: {json_file} with the current date {current_time}")

# Main function to iterate through all JSON files in the MINTAK directory
def main():
    for filename in os.listdir(MINTAK_DIR):
        if filename.endswith('.json'):
            filepath = os.path.join(MINTAK_DIR, filename)
            add_update_property(filepath)

if __name__ == '__main__':
    main()
