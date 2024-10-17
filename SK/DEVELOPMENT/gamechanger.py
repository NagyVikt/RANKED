import os
import json
import requests
from bs4 import BeautifulSoup
from config.config import api_key

# Base URL
BASE_URL = "https://www.svx.sk"

def get_html_content(url, wait_for_selector=None):
    """
    Fetches the HTML content of a given URL using ScraperAPI.

    Args:
        url (str): The URL to fetch.
        wait_for_selector (str, optional): CSS selector to wait for before rendering.

    Returns:
        str or None: The HTML content if successful, else None.
    """
    try:
        print(f"Fetching URL: {url}")
        
        # Base payload
        payload = {
            'api_key': api_key,
            'url': url,
            'render': 'true',
            'device_type': 'desktop'
        }
        
        # Add wait_for_selector if provided
        if wait_for_selector:
            payload['wait_for_selector'] = wait_for_selector
        
        response = requests.get('https://api.scraperapi.com/', params=payload)
        response.raise_for_status()
        print("Successfully fetched the URL")
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def scrape_subcategory_images(main_category_url):
    """
    Scrapes the main category page to extract subcategory slugs and their image URLs.

    Args:
        main_category_url (str): The URL of the main category page.

    Returns:
        dict: A mapping of subcategory slugs to their image URLs.
    """
    html_content = get_html_content(main_category_url, wait_for_selector=".catalog__category-tiles")
    if not html_content:
        print("Failed to retrieve main category page. Exiting.")
        exit(1)
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find the <ul> containing subcategories
    ul = soup.find('ul', class_='catalog__category-tiles')
    if not ul:
        print("Failed to find the subcategories list on the page.")
        exit(1)
    
    subcategory_image_mapping = {}
    
    # Iterate over each <li> in the <ul>
    for li in ul.find_all('li'):
        a_tag = li.find('a', href=True)
        if not a_tag:
            continue  # Skip if no <a> tag found
        
        href = a_tag['href']
        slug = href.strip('/').split('/')[-1]  # Extract slug from URL
        
        img_tag = a_tag.find('img', src=True)
        if not img_tag:
            print(f"Warning: No image found for subcategory '{slug}'. Skipping.")
            continue
        
        img_src = img_tag['src']
        # Convert relative URL to absolute
        img_url = img_src if img_src.startswith('http') else BASE_URL + img_src
        
        subcategory_image_mapping[slug] = img_url
        print(f"Found subcategory: {slug} with image URL: {img_url}")
    
    return subcategory_image_mapping

def process_subcategory_files(subcategory_folder, image_mapping, main_category_slug):
    """
    Processes each subcategory JSON file to extract subcategory information.

    Args:
        subcategory_folder (str): Path to the folder containing subcategory JSON files.
        image_mapping (dict): Mapping of subcategory slugs to image URLs.
        main_category_slug (str): The slug of the main category.

    Returns:
        list: A list of subcategory dictionaries.
    """
    subcategories = []
    
    # Iterate over each file in the subcategory folder
    for filename in os.listdir(subcategory_folder):
        # Process only JSON files that match the naming pattern
        if filename.startswith("subcategories-") and filename.endswith(".json"):
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
                        if category.get("slug") != main_category_slug:
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
                    
                    # Get the image URL from the mapping
                    img_url = image_mapping.get(subcat_slug)
                    if not img_url:
                        print(f"Warning: Image URL not found for subcategory '{subcat_slug}'. Using default image.")
                        continue  # Skip adding this subcategory
                    
                    # Construct the subcategory dictionary
                    subcategory = {
                        "id": subcat_id,
                        "slug": subcat_slug,
                        "name": subcat_name,
                        "img": img_url,
                        "link": f"https://kdtech.sk/shop/?filter_cat={subcat_slug}"
                    }
                    
                    # Check for duplicates before adding
                    if not any(sc["id"] == subcat_id for sc in subcategories):
                        subcategories.append(subcategory)
                        print(f"Added subcategory: {subcat_slug}")
                    else:
                        print(f"Notice: Subcategory '{subcat_slug}' already exists. Skipping duplicate.")
            
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON in file '{filename}': {e}")
            except Exception as e:
                print(f"Unexpected error processing file '{filename}': {e}")
    
    return subcategories

def create_main_category_json(main_category_data, subcategories, output_file):
    """
    Combines main category data with subcategories and writes to a JSON file.

    Args:
        main_category_data (dict): The main category information.
        subcategories (list): A list of subcategory dictionaries.
        output_file (str): Path to the output JSON file.
    """
    main_category_data["subcategories"] = subcategories
    
    try:
        with open(output_file, 'w', encoding='utf-8') as outfile:
            json.dump(main_category_data, outfile, ensure_ascii=False, indent=4)
        print(f"Main category JSON has been successfully created at '{output_file}'.")
    except Exception as e:
        print(f"Error writing to '{output_file}': {e}")

def main():
    # Define the main category data
    main_category = {
        "id": 87,
        "slug": "zdvihacia-technika-haky-a-retaze-tr-80-a-tr-100",
        "name": "Zdvíhacia technika, háky a reťaze tr 80 a tr 100",
        "img": "https://www.svx.sk/media/categories/category_703.jpg.100x100_q85ss0_crop_replace_alpha-%23fff.jpg.webp",
        "link": "https://kdtech.sk/shop/?filter_cat=zdvihacia-technika-haky-a-retaze-tr-80-a-tr-100",
        "subcategories": [
         
        ]
    }
    
    # URL of the main category page
    main_category_url = "https://www.svx.sk/zdvihacia-technika-haky-a-retaze-tr-80-a-tr-100/"
    
    # Path to the folder containing subcategory JSON files
    subcategory_folder = "subcategories-zdvihacia-technika-haky-a-retaze-tr-80-a-tr-100"
    
    # Check if the subcategory folder exists
    if not os.path.isdir(subcategory_folder):
        print(f"Error: The folder '{subcategory_folder}' does not exist.")
        exit(1)
    
    # Step 1: Scrape subcategory image URLs
    print("Starting to scrape subcategory image URLs...")
    image_mapping = scrape_subcategory_images(main_category_url)
    
    # Step 2: Process subcategory JSON files
    print("\nProcessing subcategory JSON files...")
    subcategories = process_subcategory_files(
        subcategory_folder=subcategory_folder,
        image_mapping=image_mapping,
        main_category_slug=main_category["slug"]
    )
    
    # Step 3: Create main category JSON
    output_file = "OUTPUT.json"
    print("\nCreating main category JSON...")
    create_main_category_json(main_category, subcategories, output_file)

if __name__ == "__main__":
    main()
