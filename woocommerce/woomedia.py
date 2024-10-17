import json
import os
import base64
import requests
from urllib.parse import urljoin
import logging
from datetime import datetime, timedelta
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("media_fetch.log"),
        logging.StreamHandler()
    ]
)

# WordPress and WooCommerce API credentials
username = 'Deadpool'
password = 'Karategi123'
wp_base_url = 'https://kdtech.hu/wp-json/'
wc_base_url = 'https://kdtech.hu/wp-json/wc/v3/'

# Encode credentials for HTTP Basic Authentication
auth_string = f'{username}:{password}'
auth_header = {
    'Authorization': 'Basic ' + base64.b64encode(auth_string.encode()).decode()
}

def parse_arguments():
    """
    Parses command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(description='Fetch and filter WooCommerce media items.')
    parser.add_argument('--folder', type=str, default='2024/10', help='Folder path to filter media items (e.g., "2024/10")')
    parser.add_argument('--days', type=int, default=10, help='Number of days to look back for recent uploads')
    return parser.parse_args()

# Function to get all media items
def get_all_media_items():
    """
    Fetches all media items from WooCommerce.

    Returns:
        list: List of media items.
    """
    url = urljoin(wp_base_url, 'wp/v2/media')
    params = {
        'per_page': 100,
        'orderby': 'date',
        'order': 'desc'  # Newest first
    }
    media_items = []
    page = 1
    while True:
        params['page'] = page
        response = requests.get(url, headers=auth_header, params=params)
        if response.status_code == 200:
            page_items = response.json()
            if not page_items:
                break  # No more media items to fetch
            media_items.extend(page_items)
            logging.info(f"Fetched page {page} with {len(page_items)} media items.")
            page += 1
        else:
            logging.error(f"Failed to retrieve media items on page {page}. Response: {response.text}")
            break
    return media_items

# Function to delete a media item
def delete_media_item(media_id):
    """
    Deletes a media item from WooCommerce.

    Args:
        media_id (int): The ID of the media item to delete.
    """
    url = urljoin(wp_base_url, f'wp/v2/media/{media_id}')
    params = {'force': True}
    response = requests.delete(url, headers=auth_header, params=params)
    if response.status_code == 200:
        logging.info(f"Media item {media_id} deleted successfully.")
    else:
        logging.error(f"Failed to delete media item {media_id}. Response: {response.text}")

# Function to filter media items by folder path and upload date
def filter_media_items(media_items, folder_path, days=10):
    """
    Filters media items based on the specified folder path and upload date within the last 'days' days.

    Args:
        media_items (list): List of media items fetched from WooCommerce.
        folder_path (str): The folder path to filter media items (e.g., '2024/10').
        days (int): Number of days to look back for recent uploads.

    Returns:
        list: Filtered list of media items.
    """
    filtered_media = []
    # Calculate the cutoff datetime
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    for item in media_items:
        source_url = item.get('source_url', '')
        upload_date_str = item.get('date', '')
        
        # Parse the upload date string to a datetime object
        try:
            upload_date = datetime.strptime(upload_date_str, '%Y-%m-%dT%H:%M:%S')
        except ValueError:
            logging.warning(f"Invalid date format for media item {item.get('id')}: {upload_date_str}")
            continue  # Skip this item if date is invalid
        
        # Check if the media item is in the specified folder and within the last 'days' days
        if folder_path in source_url and upload_date >= cutoff_date:
            filtered_media.append({
                'id': item.get('id'),
                'date': upload_date_str,
                'source_url': source_url
            })
    
    logging.info(f"Filtered {len(filtered_media)} media items containing '{folder_path}' in their URLs and uploaded in the last {days} days.")
    return filtered_media

# Function to save filtered media items with fetch timestamp to a JSON file
def save_filtered_media_to_json(filtered_media, folder_path, filename='filtered_woo_media_items.json'):
    """
    Saves filtered media items to a JSON file with a fetch timestamp.

    Args:
        filtered_media (list): List of filtered media items.
        folder_path (str): The folder path used for filtering.
        filename (str): The JSON file to save the data.
    """
    # Prepare data with fetch timestamp
    data = {
        'fetch_time': datetime.utcnow().isoformat() + 'Z',  # UTC time in ISO format
        'folder_path': folder_path,
        'media_items': filtered_media
    }
    
    try:
        # Read existing data if file exists
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        else:
            existing_data = []
        
        # Append new fetch data
        existing_data.append(data)
        
        # Save back to the JSON file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=4)
        
        logging.info(f"Filtered media items saved to {filename} with fetch time {data['fetch_time']}.")
    except Exception as e:
        logging.error(f"Failed to save filtered media items to JSON. Error: {e}")

# Optional: Function to save filtered media items to a text file
def save_filtered_media_to_txt(filtered_media, folder_path, filename='filtered_woo_media_items.txt'):
    """
    Saves filtered media item URLs to a text file.

    Args:
        filtered_media (list): List of filtered media items.
        folder_path (str): The folder path used for filtering.
        filename (str): The text file to save the URLs.
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            for item in filtered_media:
                f.write(item.get('source_url', '') + '\n')
        logging.info(f"Filtered media URLs saved to {filename}.")
    except Exception as e:
        logging.error(f"Failed to save filtered media URLs to TXT. Error: {e}")

# Main script execution
if __name__ == "__main__":
    args = parse_arguments()
    FOLDER_PATH = args.folder
    DAYS = args.days

    logging.info(f"Starting to fetch media items from WooCommerce for folder '{FOLDER_PATH}' uploaded in the last {DAYS} days...")
    all_media_items = get_all_media_items()
    if all_media_items:
        logging.info(f"Total media items fetched: {len(all_media_items)}")
        
        # Filter media items by the specified folder path and recent upload date
        filtered_media_items = filter_media_items(all_media_items, FOLDER_PATH, DAYS)
        
        if filtered_media_items:
            # Save filtered media items to JSON
            save_filtered_media_to_json(filtered_media_items, FOLDER_PATH)
            
            # Optionally, save to a text file as well
            save_filtered_media_to_txt(filtered_media_items, FOLDER_PATH)
            
            # Proceed to delete media items if desired
            # Uncomment the following lines to enable deletion
            # for media_item in filtered_media_items:
            #     delete_media_item(media_item['id'])
        else:
            logging.warning(f"No media items found in the folder '{FOLDER_PATH}' uploaded in the last {DAYS} days.")
    else:
        logging.warning("No media items fetched from WooCommerce.")
