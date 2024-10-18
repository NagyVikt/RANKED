import json
import re
import sys
import os
import unicodedata
import logging
from rapidfuzz import process, fuzz

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set to DEBUG for more detailed logs
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("script_log.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)  # Also log to console
    ]
)

def load_json_file(filepath):
    """Load a JSON file and return its content."""
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            data = json.load(file)
            logging.debug(f"Successfully loaded JSON file: {filepath}")
            return data
    except FileNotFoundError:
        logging.error(f"The file '{filepath}' was not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logging.error(f"The file '{filepath}' is not a valid JSON.\nDetails: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"An unexpected error occurred while reading '{filepath}'.\nDetails: {e}")
        sys.exit(1)

def save_json_file(data, filepath):
    """Save data to a JSON file."""
    try:
        with open(filepath, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
            logging.debug(f"Successfully saved JSON file: {filepath}")
    except Exception as e:
        logging.error(f"Error saving file '{filepath}': {e}")
        sys.exit(1)

def normalize_whitespace(text):
    """
    Replace multiple whitespace characters with a single space and strip leading/trailing spaces.
    """
    if not isinstance(text, str):
        return text  # Return as-is if not a string
    # Replace any sequence of whitespace characters with a single space
    return re.sub(r'\s+', ' ', text).strip()

def create_canonical_name(name):
    """
    Create a canonical version of the product name by:
    - Removing accents.
    - Converting to lowercase.
    - Replacing multiple spaces with a single space.
    - Stripping leading/trailing spaces.
    """
    if not isinstance(name, str):
        return ""
    # Normalize Unicode characters
    nfkd_form = unicodedata.normalize('NFKD', name)
    only_ascii = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    # Replace multiple spaces with a single space and convert to lowercase
    canonical_name = re.sub(r'\s+', ' ', only_ascii).strip().lower()
    return canonical_name

def build_name_lookup(woocommerce_products):
    """
    Build a lookup dictionary for WooCommerce products based on canonical name.
    """
    name_lookup = {}
    for product in woocommerce_products:
        name = product.get('name', '')
        # Normalize whitespace in WooCommerce names
        normalized_name = normalize_whitespace(name)
        canonical_name = create_canonical_name(normalized_name)
        if canonical_name:
            name_lookup[canonical_name] = product
            logging.debug(f"Added to lookup: '{canonical_name}'")
    logging.info(f"Built WooCommerce name lookup with {len(name_lookup)} entries.")
    return name_lookup

def build_name_lookup_magnety(magnety_products):
    """
    Build a lookup list for Magnety products based on canonical name.
    """
    magnety_canonical = []
    for product in magnety_products:
        name = product.get('name', '')
        # Normalize whitespace in Magnety names
        normalized_name = normalize_whitespace(name)
        canonical_name = create_canonical_name(normalized_name)
        # Update the product's name with normalized whitespace
        product['name'] = normalized_name
        magnety_canonical.append((product, canonical_name))
        logging.debug(f"Processed Magnety product: '{canonical_name}'")
    logging.info(f"Built Magnety canonical list with {len(magnety_canonical)} entries.")
    return magnety_canonical

def match_product(canonical_name, name_lookup, threshold=90):
    """
    Match a canonical Magnety product name to a WooCommerce product.
    """
    # Exact match
    if canonical_name in name_lookup:
        logging.debug(f"Exact match found for '{canonical_name}'")
        return name_lookup[canonical_name]

    # Fuzzy match using RapidFuzz
    match = process.extractOne(
        canonical_name,
        list(name_lookup.keys()),
        scorer=fuzz.token_sort_ratio
    )

    if match:
        best_match, score, _ = match
        logging.debug(f"Fuzzy Match: '{best_match}' with score {score} for '{canonical_name}'")
        if score >= threshold:
            return name_lookup[best_match]

    # No suitable match found
    logging.warning(f"No suitable match found for '{canonical_name}'")
    return None

def combine_categories(existing_categories, new_category):
    """
    Combine existing WooCommerce categories with the new category from magnety.json.
    Avoid duplicates based on category id.
    """
    combined = existing_categories.copy()
    new_cat_id = new_category.get('category_id')

    # Check if the new category is already present
    if not any(str(cat.get('id')) == str(new_cat_id) for cat in combined):
        # Add the new category
        combined.append({
            "id": new_category.get('category_id'),
            "name": new_category.get('category_name'),
            "slug": new_category.get('category_slug')
        })
        logging.info(f"Added new category '{new_category.get('category_name')}' (ID: {new_cat_id})")
    else:
        logging.debug(f"Category ID {new_cat_id} already exists. Skipping addition.")
    return combined

def update_woocommerce_products(woocommerce_products, magnety_products):
    """
    Update the woocommerce_products by adding new categories from magnety_products when there is a match.
    """
    # Build lookup dictionary based on canonical name for WooCommerce products
    name_lookup = build_name_lookup(woocommerce_products)

    # Build a list of canonical Magnety products
    magnety_canonical = build_name_lookup_magnety(magnety_products)

    matched_count = 0
    for product_idx, (magnety_product, canonical_name) in enumerate(magnety_canonical, start=1):
        logging.info(f"Processing Magnety Product {product_idx}: '{magnety_product.get('name', '')}'")
        matched_wc_product = match_product(canonical_name, name_lookup, threshold=90)
        if matched_wc_product:
            # Combine categories
            existing_categories = matched_wc_product.get('categories', [])
            new_category = {
                "category_id": magnety_product.get('category_id'),
                "category_name": magnety_product.get('category_name'),
                "category_slug": magnety_product.get('category_slug')
            }

            # Check if new_category has necessary fields
            if not all(new_category.values()):
                logging.warning(f"Missing category information for product '{magnety_product.get('name', '')}'. Skipping category addition.")
                continue

            combined_categories = combine_categories(existing_categories, new_category)
            # Update the matched product's categories
            matched_wc_product['categories'] = combined_categories
            matched_count += 1
            logging.info(f"Updated categories for product '{matched_wc_product.get('name', '')}' (ID: {matched_wc_product.get('id')})")
        else:
            logging.debug(f"No match found for product: '{magnety_product.get('name', '')}'")
            pass  # Do nothing for unmatched products

    logging.info(f"Total matched products: {matched_count} out of {len(magnety_canonical)}")

def main():
    # Directory containing all your Magnety JSON files
    magnety_directory = 'json'  # Update this path if necessary

    # File paths
    woocommerce_filepath = 'woocommerce_products_normalized.json'  # Normalized WooCommerce products
    output_filepath = 'woocommerce_products_updated.json'  # Output JSON file for updated WooCommerce products

    # Verify that the magnety_directory exists
    if not os.path.isdir(magnety_directory):
        logging.error(f"The directory '{magnety_directory}' does not exist.")
        sys.exit(1)
    else:
        logging.info(f"Found Magnety directory: '{magnety_directory}'")

    # Get all JSON files in the magnety_directory
    magnety_filenames = [
        filename for filename in os.listdir(magnety_directory)
        if filename.endswith('.json')
    ]

    if not magnety_filenames:
        logging.error(f"No JSON files found in the directory '{magnety_directory}'.")
        sys.exit(1)
    else:
        logging.info(f"Found {len(magnety_filenames)} JSON files in '{magnety_directory}'.")

    # Load and aggregate all Magnety products from multiple JSON files
    aggregated_magnety_products = []
    for filename in magnety_filenames:
        filepath = os.path.join(magnety_directory, filename)
        logging.info(f"Loading Magnety file: '{filepath}'")
        magnety_data = load_json_file(filepath)

        # Handle different JSON structures
        if isinstance(magnety_data, dict):
            products = magnety_data.get('products', [])
            if not products:
                logging.warning(f"No 'products' key found in '{filename}'. Attempting to use the entire dictionary as a product list.")
                # If 'products' key is missing, check if the dict itself contains product entries
                # This assumes that the dict is a list of products or contains a key that holds products
                # Modify the logic below based on your actual JSON structure
                # For simplicity, let's skip such files
                logging.warning(f"Skipping '{filename}' as it does not contain a 'products' key.")
                continue
        elif isinstance(magnety_data, list):
            products = magnety_data
        else:
            logging.warning(f"Unexpected JSON structure in '{filename}'. Skipping this file.")
            continue

        if not products:
            logging.warning(f"No products found in '{filename}'. Skipping this file.")
            continue

        aggregated_magnety_products.extend(products)
        logging.info(f"Aggregated {len(products)} products from '{filename}'.")

    if not aggregated_magnety_products:
        logging.error("No Magnety products to process after loading all files.")
        sys.exit(1)
    else:
        logging.info(f"Total aggregated Magnety products: {len(aggregated_magnety_products)}")

    # Load WooCommerce data
    logging.info(f"Loading WooCommerce data from '{woocommerce_filepath}'")
    woocommerce_data = load_json_file(woocommerce_filepath)

    # Adjusted code to handle the actual structure
    if isinstance(woocommerce_data, list) and len(woocommerce_data) > 0:
        first_element = woocommerce_data[0]
        if isinstance(first_element, dict) and 'products' in first_element:
            woocommerce_products = first_element['products']
            # Keep other data in first_element if needed
            other_data = {k: v for k, v in first_element.items() if k != 'products'}
            logging.info(f"Loaded WooCommerce products from list with first element containing 'products' key.")
        else:
            logging.error("The first element in the list does not contain 'products'.")
            sys.exit(1)
    elif isinstance(woocommerce_data, dict) and 'products' in woocommerce_data:
        woocommerce_products = woocommerce_data['products']
        other_data = {k: v for k, v in woocommerce_data.items() if k != 'products'}
        logging.info("Loaded WooCommerce products from dictionary with 'products' key.")
    else:
        logging.error("Unexpected format for 'woocommerce_products_normalized.json'. Expected a list containing a dict with 'products' key, or a dict with 'products' key.")
        sys.exit(1)

    # Update WooCommerce products with aggregated Magnety products
    logging.info(f"Updating WooCommerce products with {len(aggregated_magnety_products)} Magnety products...")
    update_woocommerce_products(woocommerce_products, aggregated_magnety_products)

    # Prepare the updated data
    updated_data = woocommerce_data  # If woocommerce_data is a dict
    if isinstance(woocommerce_data, list):
        # If it's a list, we need to update the 'products' key in the first element
        if isinstance(woocommerce_data[0], dict) and 'products' in woocommerce_data[0]:
            woocommerce_data[0]['products'] = woocommerce_products
            updated_data = woocommerce_data
            logging.info("Updated 'products' key in the first element of the WooCommerce data list.")
        else:
            logging.error("Cannot update products in WooCommerce data. The first element does not contain 'products'.")
            sys.exit(1)
    elif isinstance(woocommerce_data, dict):
        woocommerce_data['products'] = woocommerce_products
        updated_data = woocommerce_data
        logging.info("Updated 'products' key in the WooCommerce data dictionary.")
    else:
        logging.error("Unexpected structure of WooCommerce data.")
        sys.exit(1)

    # Save the updated WooCommerce products to a new JSON file
    save_json_file(updated_data, output_filepath)
    logging.info(f"Updated WooCommerce products have been saved to '{output_filepath}'")
    logging.info("Script execution completed successfully.")

if __name__ == "__main__":
    main()
