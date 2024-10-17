import json
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("filter_categories.log"),
        logging.StreamHandler()
    ]
)

def filter_categories(input_filename='woocommerce_categories.json', output_filename='filtered_categories.json'):
    """
    Reads categories from the input JSON file, extracts 'id', 'name', and 'slug' fields,
    and writes them to the output JSON file.

    Args:
        input_filename (str): The JSON file containing the full categories data.
        output_filename (str): The JSON file to write the filtered data to.
    """
    try:
        # Check if the input file exists
        if not os.path.exists(input_filename):
            logging.error(f"The input file {input_filename} does not exist.")
            return

        # Read the categories data from the input file
        with open(input_filename, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Check if data is a list (multiple fetches) or a dict (single fetch)
        if isinstance(data, list):
            all_categories = []
            for fetch in data:
                categories = fetch.get('categories', [])
                # Extract the desired fields
                filtered = [{'id': cat['id'], 'name': cat['name'], 'slug': cat['slug']} for cat in categories]
                all_categories.extend(filtered)
        elif isinstance(data, dict):
            categories = data.get('categories', [])
            # Extract the desired fields
            all_categories = [{'id': cat['id'], 'name': cat['name'], 'slug': cat['slug']} for cat in categories]
        else:
            logging.error("Unexpected data format in the input file.")
            return

        # Write the filtered categories to the output file
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(all_categories, f, ensure_ascii=False, indent=4)

        logging.info(f"Filtered categories saved to {output_filename}.")
    except Exception as e:
        logging.error(f"An error occurred while filtering categories: {e}")

if __name__ == "__main__":
    filter_categories()
