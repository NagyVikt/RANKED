import json
import re
import unicodedata
import glob
import os

def slugify(value):
    """
    Converts a string to a slug, suitable for URLs.
    """
    value = str(value)
    # Normalize unicode characters and remove accents
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    # Convert to lowercase
    value = value.lower()
    # Remove invalid characters
    value = re.sub(r'[^a-z0-9\s-]', '', value)
    # Replace multiple spaces or hyphens with a single hyphen
    value = re.sub(r'[\s-]+', '-', value)
    # Strip leading and trailing hyphens
    value = value.strip('-')
    return value

def main():
    # Initialize an empty list to hold all subcategory items
    all_subcategories = []

    # Load all subcategories JSON files starting with 'subcategories'
    for filename in glob.glob('subcategories*.json'):
        with open(filename, 'r', encoding='utf-8') as f:
            subcategories = json.load(f)
            all_subcategories.extend(subcategories)

    # Load WooCommerce products JSON
    with open('1.json', 'r', encoding='utf-8') as f:
        products = json.load(f)

    # Create a mapping from slug to subcategory data
    subcategory_slug_map = {}
    for item in all_subcategories:
        name = item.get('name', '')
        slug = slugify(name)
        subcategory_slug_map[slug] = item

    # Update products with new categories
    for product in products:
        product_slug = product.get('slug', '')
        if product_slug in subcategory_slug_map:
            subcategory_item = subcategory_slug_map[product_slug]
            # Get existing and new categories
            existing_categories = product.get('categories', [])
            new_categories = subcategory_item.get('categories', [])
            # Avoid duplicates by checking category IDs
            existing_category_ids = {cat['id'] for cat in existing_categories}
            for cat in new_categories:
                if cat['id'] not in existing_category_ids:
                    existing_categories.append(cat)
            # Update the product's categories
            product['categories'] = existing_categories

    # Save the updated products to a new JSON file
    with open('2.json', 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    main()
