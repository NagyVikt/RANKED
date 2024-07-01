import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
from collections import deque
import time

# Configuration
API_KEY = 'AIzaSyDMitVW0KIxe9mK6evYm7gsAxh_zm4CS-U'
CSE_ID = '9225504b95b334f88'
SCRAPER_API_KEY = '6667a4085b3eaf440230e75290783fa5'

# Function to perform Google search
def google_search(query, api_key, cse_id):
    url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={api_key}&cx={cse_id}"
    response = requests.get(url)
    results = response.json()
    return results

def extract_ranking_data(results):
    ranking_data = []
    for i, item in enumerate(results.get('items', [])):
        ranking_data.append({
            'rank': i + 1,
            'title': item['title'],
            'link': item['link']
        })
    return ranking_data

# Function to get HTML content
def get_html_content(url):
    try:
        response = requests.get(f'http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={url}')
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

# Function to extract emails
def extract_emails(html_content):
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
    emails = re.findall(email_pattern, html_content)
    return emails

# Function to get internal links
def get_internal_links(base_url, html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    links = set()
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        full_url = urljoin(base_url, href)
        if urlparse(full_url).netloc == urlparse(base_url).netloc:
            links.add(full_url)
    return links

def should_crawl(url):
    keywords = ['contact', 'about', 'impressum', 'team', 'support']
    return any(keyword in url.lower() for keyword in keywords)

def crawl(url, max_depth=2):
    visited_urls = set()
    email_results = []
    queue = deque([(url, 0)])

    while queue:
        current_url, depth = queue.popleft()
        
        if current_url in visited_urls or depth > max_depth:
            continue
        
        visited_urls.add(current_url)
        print(f"Crawling URL: {current_url}")
        html_content = get_html_content(current_url)
        if html_content:
            emails = extract_emails(html_content)
            emails = [email for email in emails if not re.search(r'\.(png|jpg|jpeg|webp|gif)$', email)]
            if emails:
                print(f"Emails found in {current_url}: {emails}")
                email_results.extend(emails)

            if depth < max_depth:
                internal_links = get_internal_links(current_url, html_content)
                for link in internal_links:
                    if should_crawl(link):
                        queue.append((link, depth + 1))
        time.sleep(0.5)

    return email_results

def main():
    query = ""
    search_results = google_search(query, API_KEY, CSE_ID)
    ranking_data = extract_ranking_data(search_results)
    
    all_emails = []
    for data in ranking_data:
        url = data['link']
        emails = crawl(url)
        all_emails.extend(emails)
    
    unique_emails = set(all_emails)
    print(f"Total unique emails found: {unique_emails}")

if __name__ == "__main__":
    main()
