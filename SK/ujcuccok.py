
import json 

output_json_filename = 'rebriky-alve.json'

# Function to load existing products from the JSON file
def load_existing_products(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            existing_products = json.load(f)
            existing_urls = {product['link'] for product in existing_products}
            return existing_urls
    except FileNotFoundError:
        return set()  # Return an empty set if the file doesn't exist


# Main script execution
if __name__ == "__main__":
    existing_product_urls = load_existing_products(output_json_filename)

    # Create or clear the JSON file before starting the scraping process
    with open(output_json_filename, 'w', encoding='utf-8') as f:
        f.write('[\n')

    for page_number in range(1, total_pages + 1):
        category_url = f"{base_category_url}?p={page_number}"
        print(f"Processing page {page_number} of {total_pages}: {category_url}")

        product_infos = extract_product_info_from_category_page(category_url)

        for product_info in product_infos:
            if product_info['link'] in existing_product_urls:
                print(f"Skipping existing product: {product_info['name']}")
                continue

            print(f"New product found: {product_info['name']}")
            full_product_info = fetch_additional_details(product_info)
            if full_product_info:
                save_product_to_json(full_product_info)
    
    with open(output_json_filename, 'a', encoding='utf-8') as f:
        f.write(']')

    print(f"Scraping completed and data saved to {output_json_filename}")
