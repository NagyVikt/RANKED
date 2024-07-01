import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
from collections import deque
import time

# ScraperAPI key
api_key = '6667a4085b3eaf440230e75290783fa5'

# List of URLs to scrape
start_urls = [
    'https://www.prva.sk/telefon.aspx',
    # Add more URLs as needed
]

visited_urls = set()
email_results = []

def get_html_content(url):
    try:
        response = requests.get(f'http://api.scraperapi.com?api_key={api_key}&url={url}')
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def extract_emails(html_content):
    # Improved regex pattern for extracting emails
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
    emails = re.findall(email_pattern, html_content)
    # Print all matches for debugging
    print(f"All matches found: {emails}")
    return emails

def get_internal_links(base_url, html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    links = set()
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        full_url = urljoin(base_url, href)
        if urlparse(full_url).netloc == urlparse(base_url).netloc:  # Ensure it's an internal link
            links.add(full_url)
    return links

def should_crawl(url):
    keywords = ['contact', 'about', 'impressum', 'team', 'support']
    return any(keyword in url.lower() for keyword in keywords)

def crawl(url, max_depth=2):
    queue = deque([(url, 0)])
    
    while queue:
        current_url, depth = queue.popleft()
        
        if current_url in visited_urls or depth > max_depth:
            continue
        
        visited_urls.add(current_url)
        print(f"Crawling URL: {current_url}")  # Debugging line
        html_content = get_html_content(current_url)
        if html_content:
            # Save the HTML content for debugging
            with open('debug.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            emails = extract_emails(html_content)
            # Filter out false positives
            emails = [email for email in emails if not re.search(r'\.(png|jpg|jpeg|webp|gif)$', email)]
            if emails:
                print(f"Emails found in {current_url}: {emails}")
                if emails not in email_results:
                    email_results.extend(emails)

            if depth < max_depth:
                internal_links = get_internal_links(current_url, html_content)
                for link in internal_links:
                    if should_crawl(link):
                        queue.append((link, depth + 1))
        # Be polite to the server
        time.sleep(0.5)

def main(urls):
    for url in urls:
        crawl(url)
    print(f"Total emails found: {set(email_results)}")

if __name__ == "__main__":
    main(start_urls)
