import os
import json

# Define the main category data
main_category = {
    "id": 98,
    "slug": "domacnost-a-drogeria",
    "name": "Domácnosť a drogéria",
    "img": "https://www.svx.sk/media/categories/category_1261.jpg.100x100_q85ss0_crop_replace_alpha-%23fff.jpg.webp",
    "link": "https://kdtech.sk/shop/?filter_cat=domacnost-a-drogeria",
    "subcategories": []
}

# Path to the folder containing subcategory JSON files
subcategory_folder = "subcategories-domacnost-a-drogeria"

# Ensure the subcategory folder exists
if not os.path.isdir(subcategory_folder):
    print(f"Error: The folder '{subcategory_folder}' does not exist.")
    exit(1)

# Iterate over each file in the subcategory folder
for filename in os.listdir(subcategory_folder):
    # Process only JSON files that match the naming pattern
    if filename.startswith("subcategories-domacnost-a-drogeria-") and filename.endswith(".json"):
        file_path = os.path.join(subcategory_folder, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                products = json.load(file)
                
                if not products:
                    print(f"Warning: The file '{filename}' is empty. Skipping.")
                    continue
                
                # Assume all products in the file belong to the same subcategory
                first_product = products[0]
                categories = first_product.get("categories", [])
                
                # Find the subcategory (excluding the main category)
                subcategory_info = None
                for category in categories:
                    if category.get("slug") != main_category["slug"]:
                        subcategory_info = category
                        break
                
                if not subcategory_info:
                    print(f"Warning: No subcategory found in '{filename}'. Skipping.")
                    continue
                
                subcat_id = subcategory_info.get("id")
                subcat_slug = subcategory_info.get("slug")
                subcat_name = subcategory_info.get("name")
                
                if not all([subcat_id, subcat_slug, subcat_name]):
                    print(f"Warning: Missing subcategory fields in '{filename}'. Skipping.")
                    continue
                
                # Construct the subcategory dictionary
                subcategory = {
                    "id": subcat_id,
                    "slug": subcat_slug,
                    "name": subcat_name,
                    "img": main_category["img"],  # Constant image URL
                    "link": f"https://kdtech.sk/shop/?filter_cat={subcat_slug}"
                }
                
                # Check for duplicates before adding
                if not any(sc["id"] == subcat_id for sc in main_category["subcategories"]):
                    main_category["subcategories"].append(subcategory)
                else:
                    print(f"Notice: Subcategory '{subcat_slug}' already exists. Skipping duplicate.")
        
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON in file '{filename}': {e}")
        except Exception as e:
            print(f"Unexpected error processing file '{filename}': {e}")

# Path to the output main category JSON file
output_file = "OUTPUT.json"

# Write the main category data to the output JSON file
try:
    with open(output_file, 'w', encoding='utf-8') as outfile:
        json.dump(main_category, outfile, ensure_ascii=False, indent=4)
    print(f"Main category JSON has been successfully created at '{output_file}'.")
except Exception as e:
    print(f"Error writing to '{output_file}': {e}")
