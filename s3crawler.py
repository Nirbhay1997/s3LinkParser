import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
from collections import deque
import time

def crawl_domain_for_s3_urls(start_url, max_pages=100):
    # Parsed domain of the start URL
    domain = urlparse(start_url).netloc

    # Initialize queue with the start URL
    queue = deque([start_url])
    visited = set()
    s3_urls_found = set()

    # Regular expression pattern for matching S3 URLs
    s3_pattern = r'https?://[^/]*s3[^/]*\.amazonaws\.com[^ "\'>]*'

    headers = {'User-Agent': 'Mozilla/5.0 (compatible; S3UrlCrawler/1.0)'}

    while queue and len(visited) < max_pages:
        url = queue.popleft()
        if url in visited:
            continue
        visited.add(url)
        print(f'Crawling: {url}')

        try:
            response = requests.get(url, headers=headers, timeout=10)
            content = response.text
        except requests.exceptions.RequestException as e:
            print(f'Error fetching {url}: {e}')
            continue

        # Find all S3 URLs in the content
        s3_urls_in_content = re.findall(s3_pattern, content)
        s3_urls_found.update(s3_urls_in_content)

        # Parse the HTML content
        soup = BeautifulSoup(content, 'html.parser')

        # Collect all URLs from href and src attributes
        tags_attrs = {
            'a': 'href',
            'img': 'src',
            'script': 'src',
            'link': 'href',
        }

        for tag, attr in tags_attrs.items():
            for element in soup.find_all(tag):
                url_attr = element.get(attr)
                if url_attr:
                    full_url = urljoin(url, url_attr)
                    parsed_full_url = urlparse(full_url)

                    # Ensure the URL is within the same domain
                    if parsed_full_url.netloc == domain:
                        if full_url not in visited:
                            queue.append(full_url)

        # Respectful crawling: Sleep to prevent overloading the server
        time.sleep(0.5)

    return s3_urls_found

if __name__ == '__main__':
    start_url = input('Enter the starting URL (e.g., https://example.com): ')
    max_pages = int(input('Enter the maximum number of pages to crawl: '))
    s3_urls = crawl_domain_for_s3_urls(start_url, max_pages)
    if s3_urls:
        print('\nFound S3 URLs:')
        for u in s3_urls:
            print(u)
    else:
        print('No S3 URLs found.')
