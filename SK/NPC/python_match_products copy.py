import json
import re
import sys
import os
import unicodedata
from rapidfuzz import process, fuzz

def load_json_file(filepath):
    """Load a JSON file and return its content."""
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: The file '{filepath}' was not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: The file '{filepath}' is not a valid JSON.\nDetails: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: An unexpected error occurred while reading '{filepath}'.\nDetails: {e}")
        sys.exit(1)

def save_json_file(data, filepath):
    """Save data to a JSON file."""
    try:
        with open(filepath, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error saving file '{filepath}': {e}")
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
    Also, create a list of canonical names for fuzzy matching.
    """
    name_lookup = {}
    canonical_names = []
    for product in woocommerce_products:
        name = product.get('name', '')
        # Normalize whitespace in WooCommerce names
        normalized_name = normalize_whitespace(name)
        canonical_name = create_canonical_name(normalized_name)
        if canonical_name:
            name_lookup[canonical_name] = product
            canonical_names.append(canonical_name)
            # Debug: Print canonical WooCommerce names
            print(f"Canonical WooCommerce Name: '{canonical_name}'")
    return name_lookup, canonical_names

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
        print(f"Canonical Magnety Name: '{canonical_name}'")
    return magnety_canonical

def match_product(canonical_name, name_lookup, threshold=90):
    """
    Match a canonical Magnety product name to a WooCommerce product.
    """
    # Exact match
    if canonical_name in name_lookup:
        print(f"Exact match found for '{canonical_name}'")
        return name_lookup[canonical_name]

    # Fuzzy match using RapidFuzz
    match = process.extractOne(
        canonical_name,
        list(name_lookup.keys()),
        scorer=fuzz.token_sort_ratio
    )

    if match:
        best_match, score, _ = match
        print(f"Fuzzy Match: '{best_match}' with score {score}")
        if score >= threshold:
            return name_lookup[best_match]

    # No suitable match found
    return None

def combine_categories(existing_categories, new_category):
    """
    Combine existing WooCommerce categories with the new category from magnety.json.
    Avoid duplicates based on category id.
    """
    combined = existing_categories.copy()
    new_cat_id = new_category.get('category_id')

    # Check if the new category is already present
    if not any(cat.get('id') == new_cat_id for cat in combined):
        # Add the new category
        combined.append({
            "id": new_category.get('category_id'),
            "name": new_category.get('category_name'),
            "slug": new_category.get('category_slug')
        })
    return combined

def main():
    # File paths (update these paths as needed)
    magnety_filepath = 'magnety.json'  # The JSON file with your Magnety products
    woocommerce_filepath = 'woocommerce_products_normalized.json'  # Normalized WooCommerce products
    output_filepath = 'matched_magnety.json'  # Output JSON file for matched products
    unmatched_output_filepath = 'unmatched_magnety.json'  # Optional: Output for unmatched products

    # Load JSON data
    magnety_data = load_json_file(magnety_filepath)
    woocommerce_data = load_json_file(woocommerce_filepath)

    # Adjusted code to handle the actual structure
    if isinstance(woocommerce_data, list) and len(woocommerce_data) > 0:
        first_element = woocommerce_data[0]
        if isinstance(first_element, dict) and 'products' in first_element:
            woocommerce_products = first_element['products']
        else:
            print("Error: The first element in the list does not contain 'products'.")
            sys.exit(1)
    elif isinstance(woocommerce_data, dict) and 'products' in woocommerce_data:
        woocommerce_products = woocommerce_data['products']
    else:
        print("Error: Unexpected format for 'woocommerce_products_normalized.json'. Expected a list containing a dict with 'products' key, or a dict with 'products' key.")
        sys.exit(1)

    print(f"\nNumber of WooCommerce products loaded: {len(woocommerce_products)}\n")

    # Build lookup dictionary based on canonical name for WooCommerce products
    name_lookup, canonical_names = build_name_lookup(woocommerce_products)

    print(f"\nNumber of canonical WooCommerce product names: {len(canonical_names)}\n")

    # Build a list of canonical Magnety products
    magnety_products = magnety_data.get('products', [])
    magnety_canonical = build_name_lookup_magnety(magnety_products)

    # Prepare lists for matched and unmatched products
    matched_products = []
    unmatched_products = []

    # Iterate over Magnety products and attempt to match with WooCommerce products
    for product_idx, (magnety_product, canonical_name) in enumerate(magnety_canonical, start=1):
        print(f"\nProcessing Magnety Product {product_idx}: '{magnety_product.get('name', '')}'")
        matched_wc_product = match_product(canonical_name, name_lookup, threshold=90)
        if matched_wc_product:
            # Combine categories
            existing_categories = matched_wc_product.get('categories', [])
            new_category = {
                "category_id": magnety_product.get('category_id'),
                "category_name": magnety_product.get('category_name'),
                "category_slug": magnety_product.get('category_slug')
            }
            combined_categories = combine_categories(existing_categories, new_category)

            # Create the new product entry with slug from magnety.json
            new_product_entry = {
                "id": matched_wc_product.get('id'),
                "name": matched_wc_product.get('name'),
                "slug": normalize_whitespace(magnety_product.get('slug', '')),  # Normalize slug as well
                "categories": combined_categories
            }

            matched_products.append(new_product_entry)
            print(f"Matched: '{magnety_product.get('name')}' -> ID: {matched_wc_product.get('id')}\n")
        else:
            print(f"No match found for product: '{magnety_product.get('name')}'\n")
            # Optional: Collect unmatched products
            unmatched_products.append({
                "name": magnety_product.get('name'),
                "slug": magnety_product.get('slug'),
                "category_id": magnety_product.get('category_id'),
                "category_name": magnety_product.get('category_name'),
                "category_slug": magnety_product.get('category_slug')
            })

    # Save the matched products to a new JSON file
    save_json_file(matched_products, output_filepath)
    print(f"\nMatched products have been saved to '{output_filepath}'")

    # Optional: Save unmatched products to a separate file for manual review
    if unmatched_products:
        save_json_file(unmatched_products, unmatched_output_filepath)
        print(f"Unmatched products have been saved to '{unmatched_output_filepath}'")

    # Optional: Save the normalized Magnety data back to a file
    magnety_data['products'] = [product for product, _ in magnety_canonical]
    save_json_file(magnety_data, 'magnety_normalized.json')
    print(f"Normalized Magnety data has been saved to 'magnety_normalized.json'")

if __name__ == "__main__":
    main()
