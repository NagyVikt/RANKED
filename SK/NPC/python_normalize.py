import json
import re
import sys
import os

def normalize_whitespace(text):
    """
    Replace multiple whitespace characters with a single space.
    
    Parameters:
    - text (str): The text to normalize.
    
    Returns:
    - str: The normalized text with single spaces.
    """
    if not isinstance(text, str):
        return text  # Return as-is if not a string
    # Replace any sequence of whitespace characters with a single space
    return re.sub(r'\s+', ' ', text).strip()

def normalize_product_names(input_filepath, output_filepath):
    """
    Normalize the 'name' field in each product within the JSON file.
    
    Parameters:
    - input_filepath (str): Path to the original woocommerce_products.json
    - output_filepath (str): Path where the normalized JSON will be saved
    """
    # Check if input file exists
    if not os.path.isfile(input_filepath):
        print(f"Error: The file '{input_filepath}' does not exist.")
        sys.exit(1)
    
    try:
        with open(input_filepath, 'r', encoding='utf-8') as infile:
            data = json.load(infile)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to decode JSON from '{input_filepath}'.\nDetails: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: An unexpected error occurred while reading '{input_filepath}'.\nDetails: {e}")
        sys.exit(1)
    
    # Verify that the top-level structure is a list
    if not isinstance(data, list):
        print("Error: Expected the top-level JSON structure to be a list.")
        sys.exit(1)
    
    total_products = 0
    normalized_count = 0
    
    # Iterate over each item in the top-level list
    for item_idx, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            print(f"Warning: Item {item_idx} in the top-level list is not a dictionary and was skipped.")
            continue
        
        # Check if 'products' key exists and is a list
        products = item.get('products', [])
        if not isinstance(products, list):
            print(f"Warning: 'products' key in item {item_idx} is not a list and was skipped.")
            continue
        
        print(f"\nProcessing 'products' in item {item_idx}: {len(products)} product(s) found.")
        
        # Iterate over each product in the 'products' list
        for product_idx, product in enumerate(products, start=1):
            total_products += 1
            if 'name' in product:
                original_name = product['name']
                normalized_name = normalize_whitespace(original_name)
                if original_name != normalized_name:
                    product['name'] = normalized_name
                    normalized_count += 1
                    print(f"  Product {product_idx}:")
                    print(f"    Original: '{original_name}'")
                    print(f"    Normalized: '{normalized_name}'\n")
                else:
                    print(f"  Product {product_idx}: Name is already normalized.")
            else:
                print(f"  Product {product_idx}: Warning - 'name' field is missing and was skipped.\n")
    
    # Save the normalized data to the output file
    try:
        with open(output_filepath, 'w', encoding='utf-8') as outfile:
            json.dump(data, outfile, ensure_ascii=False, indent=4)
        print(f"\nNormalization complete. {normalized_count} out of {total_products} product names were normalized.")
        print(f"Normalized data has been saved to '{output_filepath}'.\n")
    except Exception as e:
        print(f"Error: Failed to write to '{output_filepath}'.\nDetails: {e}")
        sys.exit(1)

def main():
    """
    Main function to execute the normalization script.
    """
    # Define default file paths
    default_input = 'woocommerce_products.json'
    default_output = 'woocommerce_products_normalized.json'
    
    # Parse command-line arguments for custom file paths (optional)
    args = sys.argv[1:]
    if len(args) == 0:
        input_filepath = default_input
        output_filepath = default_output
    elif len(args) == 2:
        input_filepath, output_filepath = args
    else:
        print("Usage: python normalize_woocommerce_names.py [input_json output_json]")
        print(f"Example: python normalize_woocommerce_names.py {default_input} {default_output}")
        sys.exit(1)
    
    normalize_product_names(input_filepath, output_filepath)

if __name__ == "__main__":
    main()
