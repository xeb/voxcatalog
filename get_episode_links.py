#!/usr/bin/env python3
"""
Script to scrape episode links from Voxology podcast website.
Navigates through all pages and extracts episode links from "Listen to the episode" anchor tags.
"""

import requests
from bs4 import BeautifulSoup
import time
import sys
import json
from datetime import datetime
import os
from tqdm import tqdm

def load_existing_data():
    """Load existing episode data from JSON file."""
    if os.path.exists('episodes.json'):
        try:
            with open('episodes.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading existing data: {e}")
            return {"episodes": [], "processed_pages": [], "last_updated": None}
    else:
        return {"episodes": [], "processed_pages": [], "last_updated": None}

def save_data(data):
    """Save episode data to JSON file."""
    data["last_updated"] = datetime.now().isoformat()
    try:
        with open('episodes.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"Error saving data: {e}")

def is_404_page(html_content):
    """Check if the page is actually a 404 error page."""
    # Look for actual 404 error indicators in the page title or specific error content
    lower_content = html_content.lower()
    return (
        "page not found" in lower_content or
        "404 error" in lower_content or
        "<title>404" in lower_content or
        "not found" in lower_content and "error" in lower_content
    )

def get_page_content(url, retry_with_sleep=False):
    """Fetch page content with error handling."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Attempting to fetch: {url}")
        print(f"Response status: {response.status_code}")
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        if retry_with_sleep:
            print("Sleeping 5 seconds before final exit...")
            time.sleep(5)
        return None

def extract_episode_links(html_content, page_num=1):
    """Extract episode links from page content."""
    soup = BeautifulSoup(html_content, 'html.parser')
    episodes = []
    
    # Debug: Save HTML to file for inspection (only for first page)
    if page_num == 1 and not os.path.exists('debug_page.html'):
        with open('debug_page.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        print("Saved page HTML to debug_page.html for inspection")
    
    # Use the specific CSS selector pattern provided: .card-body a.mt-4[href]
    # Find all card-body elements
    card_bodies = soup.find_all('div', class_='card-body')
    print(f"Found {len(card_bodies)} card-body elements")
    
    for card_body in card_bodies:
        # Look for links with class 'mt-4' within each card-body
        episode_link = card_body.find('a', class_='mt-4', href=True)
        
        if episode_link:
            href = episode_link.get('href')
            
            # Try to get the episode title from the h3 heading in the same card-body
            title_element = card_body.find('h3')
            title = None
            if title_element:
                title_link = title_element.find('a')
                if title_link:
                    title = title_link.get_text(strip=True)
                else:
                    title = title_element.get_text(strip=True)
            
            if href:
                # Make sure it's a full URL
                if href.startswith('/'):
                    full_url = 'https://www.voxologypodcast.com' + href
                else:
                    full_url = href
                
                episode_data = {
                    "url": full_url,
                    "page": page_num,
                    "title": title
                }
                episodes.append(episode_data)
                print(f"Found episode: {full_url} - {title}")
    
    # Fallback: if the above doesn't work, try the broader approach
    if not episodes:
        print("Primary selector didn't work, trying fallback...")
        # Look for "Listen to the Episode" links specifically
        listen_links = soup.find_all('a', string=lambda x: x and 'listen to the episode' in x.lower())
        for link in listen_links:
            href = link.get('href')
            if href:
                if href.startswith('/'):
                    href = 'https://www.voxologypodcast.com' + href
                episode_data = {
                    "url": href,
                    "page": page_num,
                    "title": None
                }
                episodes.append(episode_data)
                print(f"Found via 'Listen' text: {href}")
        
        # Also try finding links with 'mt-4' class anywhere
        if not episodes:
            mt4_links = soup.find_all('a', class_='mt-4', href=True)
            for link in mt4_links:
                href = link.get('href')
                if href and href.startswith('/') and href != '/':
                    full_url = 'https://www.voxologypodcast.com' + href
                    episode_data = {
                        "url": full_url,
                        "page": page_num,
                        "title": None
                    }
                    episodes.append(episode_data)
                    print(f"Found mt-4 link: {full_url}")
    
    print(f"Total episode links found on page {page_num}: {len(episodes)}")
    
    return episodes

def main():
    """Main function to scrape all episode links."""
    base_url = "https://www.voxologypodcast.com/episodes/"
    
    print("Starting to scrape Voxology podcast episodes...")
    
    # Load existing data
    data = load_existing_data()
    processed_pages = set(data["processed_pages"])
    
    if processed_pages:
        print(f"Found existing data with {len(data['episodes'])} episodes from pages: {sorted(processed_pages)}")
    
    # Test different URL patterns first (only if we haven't found a working one)
    test_urls = [
        "https://www.voxologypodcast.com/episodes/",
        "https://www.voxologypodcast.com/episodes",
        "https://voxologypodcast.com/episodes/",
        "https://voxologypodcast.com/episodes",
    ]
    
    working_base_url = None
    for test_url in test_urls:
        if 1 in processed_pages:
            # We already know this works if page 1 was processed
            working_base_url = "https://www.voxologypodcast.com/episodes/"
            break
        
        print(f"Testing URL: {test_url}")
        content = get_page_content(test_url)
        if content:
            working_base_url = test_url
            print(f"✓ Working URL found: {test_url}")
            break
    
    if not working_base_url:
        print("❌ Could not find a working episodes URL")
        return
    
    # Create overall progress bar for page processing (total 23 pages)
    total_pages = 23
    with tqdm(
        total=total_pages,
        desc="📄 Pages Progress",
        unit="pages",
        ncols=100,
        position=0
    ) as overall_pbar:
        
        # Update progress bar for already processed pages
        overall_pbar.update(len(processed_pages))
        
        # Process page 1 if not already done
        if 1 not in processed_pages:
            print("Processing page 1...")
            html_content = get_page_content(working_base_url)
            if html_content:
                episodes = extract_episode_links(html_content, 1)
                data["episodes"].extend(episodes)
                data["processed_pages"].append(1)
                
                # Save after each page
                save_data(data)
                print(f"Found {len(episodes)} episodes on page 1")
                overall_pbar.update(1)  # Update progress bar
                
                # Only continue if we found episodes on page 1
                if len(episodes) == 0:
                    print("No episodes found on page 1. Check debug_page.html for HTML structure.")
                    return
            else:
                print("Could not fetch page 1")
                overall_pbar.update(1)  # Update progress even on failure
                return
        else:
            print("Page 1 already processed, skipping...")
        
        # Try different pagination URL patterns (only if we need to)
        pagination_patterns = [
            f"{working_base_url}?page={{}}",
            f"{working_base_url.rstrip('/')}/page/{{}}/" if working_base_url.endswith('/') else f"{working_base_url}/page/{{}}/",
            f"{working_base_url.rstrip('/')}/{{}}/" if working_base_url.endswith('/') else f"{working_base_url}/{{}}/",
        ]
        
        # Find working pagination pattern (skip if we already know it works)
        working_pagination_pattern = f"{working_base_url}?page={{}}"  # Default based on user feedback
        
        if 2 not in processed_pages:
            # Test page 2 with different patterns to find the working one
            for pattern in pagination_patterns:
                test_url = pattern.format(2)
                print(f"Testing pagination pattern: {test_url}")
                content = get_page_content(test_url)
                if content and not is_404_page(content):
                    working_pagination_pattern = pattern
                    print(f"✓ Working pagination pattern: {pattern}")
                    break
        
        # Process remaining pages
        failed_pages = 0
        for page_num in range(2, 24):
            if page_num in processed_pages:
                print(f"Page {page_num} already processed, skipping...")
                continue
                
            print(f"Processing page {page_num}...")
            page_url = working_pagination_pattern.format(page_num)
            
            # Try to fetch the page, with retry logic
            html_content = get_page_content(page_url)
            if not html_content:
                # Retry once with sleep
                print(f"Failed to fetch page {page_num}, retrying with sleep...")
                html_content = get_page_content(page_url, retry_with_sleep=True)
                
            if html_content and not is_404_page(html_content):
                episodes = extract_episode_links(html_content, page_num)
                data["episodes"].extend(episodes)
                data["processed_pages"].append(page_num)
                
                # Save after each page
                save_data(data)
                print(f"Found {len(episodes)} episodes on page {page_num}")
                overall_pbar.update(1)  # Update progress bar
                
                # Stop if no episodes found (likely reached end)
                if len(episodes) == 0:
                    print(f"No episodes found on page {page_num}, stopping pagination")
                    break
                    
                failed_pages = 0  # Reset failure counter on success
            else:
                failed_pages += 1
                print(f"Page {page_num} not found or empty")
                overall_pbar.update(1)  # Update progress even on failure
                
                # Stop if we have too many consecutive failures
                if failed_pages >= 3:
                    print(f"Too many consecutive failures, stopping pagination")
                    break
            
            # Be respectful with requests
            time.sleep(1)
    
    # Final summary
    total_episodes = len(data["episodes"])
    total_pages = len(data["processed_pages"])
    
    print(f"\nCompleted! Found {total_episodes} total episodes across {total_pages} pages.")
    print("Episode data saved to 'episodes.json'")
    print(f"Processed pages: {sorted(data['processed_pages'])}")

if __name__ == "__main__":
    main()