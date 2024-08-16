import json
import os
import base64
import requests
from urllib.parse import urljoin
import re


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

# Function to get all media items
def get_all_media_items():
    url = urljoin(wp_base_url, 'wp/v2/media')
    params = {'per_page': 100}
    response = requests.get(url, headers=auth_header, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to retrieve media items. Response: {response.text}")
        return []

# Function to delete a media item
def delete_media_item(media_id):
    url = urljoin(wp_base_url, f'wp/v2/media/{media_id}')
    params = {'force': True}
    response = requests.delete(url, headers=auth_header, params=params)
    if response.status_code == 200:
        print(f"Media item {media_id} deleted successfully.")
    else:
        print(f"Failed to delete media item {media_id}. Response: {response.text}")

# Main script execution
if __name__ == "__main__":
    media_items = get_all_media_items()
    for media_item in media_items:
        delete_media_item(media_item['id'])
