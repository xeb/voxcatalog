#!/usr/bin/env python3
"""
Script to extract MP3 audio links from Voxology podcast episode pages.
Reads episode URLs from episodes.json and adds audio_link field to each record.
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
import sys
from collections import defaultdict
from tqdm import tqdm

def load_episodes_data():
    """Load episode data from episodes.json."""
    try:
        with open('episodes.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: episodes.json not found. Run get_episode_links.py first.")
        sys.exit(1)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading episodes.json: {e}")
        sys.exit(1)

def save_episodes_data(data):
    """Save updated episode data back to episodes.json."""
    data["last_updated"] = datetime.now().isoformat()
    try:
        with open('episodes.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"Error saving episodes.json: {e}")

def get_page_content(url, retry_with_sleep=False):
    """Fetch page content with error handling."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        if retry_with_sleep:
            print("Sleeping 5 seconds before continuing...")
            time.sleep(5)
        return None

def extract_audio_link(html_content, episode_url):
    """Extract MP3 or M4A audio link from episode page content."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Look for audio source tags with MP3 or M4A files (type="audio/mp3" can contain M4A files)
    audio_sources = soup.find_all('source', {'type': 'audio/mp3'})
    
    for source in audio_sources:
        src = source.get('src')
        if src and ('.mp3' in src or '.m4a' in src):
            return src
    
    # Look for audio source tags with M4A type
    audio_sources_m4a = soup.find_all('source', {'type': 'audio/m4a'})
    
    for source in audio_sources_m4a:
        src = source.get('src')
        if src and ('.mp3' in src or '.m4a' in src):
            return src
    
    # Fallback: look for any source tag with MP3 or M4A in the src
    all_sources = soup.find_all('source')
    for source in all_sources:
        src = source.get('src')
        if src and ('.mp3' in src or '.m4a' in src):
            return src
    
    # Fallback: look for audio tags with MP3 or M4A src
    audio_tags = soup.find_all('audio')
    for audio in audio_tags:
        src = audio.get('src')
        if src and ('.mp3' in src or '.m4a' in src):
            return src
    
    # Fallback: look for any link that might be an MP3 or M4A
    links = soup.find_all('a', href=True)
    for link in links:
        href = link.get('href')
        if href and ('.mp3' in href or '.m4a' in href):
            return href
    
    print(f"No MP3 or M4A audio link found on {episode_url}")
    return None

def group_episodes_by_page(episodes):
    """Group episodes by page number for batch processing."""
    pages = defaultdict(list)
    for episode in episodes:
        pages[episode['page']].append(episode)
    return pages

def main():
    """Main function to extract audio links for all episodes."""
    print("Starting audio link extraction process...")
    
    # Load episode data
    data = load_episodes_data()
    episodes = data.get('episodes', [])
    
    if not episodes:
        print("No episodes found in episodes.json")
        return
    
    # Group episodes by page for batch processing
    pages = group_episodes_by_page(episodes)
    total_pages = len(pages)
    total_episodes = len(episodes)
    
    print(f"Found {total_episodes} episodes across {total_pages} pages")
    
    # Track progress
    processed_count = 0
    skipped_count = 0
    failed_count = 0
    
    # Create overall progress bar for all episodes
    with tqdm(
        total=total_episodes,
        desc="🎵 Audio Links Progress",
        unit="episodes",
        ncols=100,
        position=0
    ) as overall_pbar:
        
        # Process each page as a batch
        for page_num in sorted(pages.keys()):
            page_episodes = pages[page_num]
            
            print(f"\nProcessing page {page_num} ({len(page_episodes)} episodes)...")
            
            # Check which episodes already have audio links and which need them
            episodes_with_audio = [ep for ep in page_episodes if 'audio_link' in ep and ep['audio_link']]
            episodes_needing_audio = [ep for ep in page_episodes if 'audio_link' not in ep or not ep['audio_link']]
            
            # Show episodes that already have audio links (skipped)
            if episodes_with_audio:
                print(f"  Episodes already processed ({len(episodes_with_audio)}):")
                for episode in episodes_with_audio:
                    title = episode.get('title', 'Unknown')
                    print(f"    ✅ {title}")
                    overall_pbar.update(1)  # Update progress bar for skipped episodes
                skipped_count += len(episodes_with_audio)
            
            if not episodes_needing_audio:
                print(f"  All episodes on page {page_num} already have audio links, moving to next page...")
                continue
            
            # Show episodes that need processing
            print(f"  Episodes to process ({len(episodes_needing_audio)}):")
            for episode in episodes_needing_audio:
                title = episode.get('title', 'Unknown')
                print(f"    🔍 {title}")
            
            # Process episodes that need audio links
            for episode in episodes_needing_audio:
                url = episode['url']
                title = episode.get('title', 'Unknown')
                
                # Get the episode page content
                html_content = get_page_content(url)
                if not html_content:
                    # Retry once with sleep
                    html_content = get_page_content(url, retry_with_sleep=True)
                
                if html_content:
                    # Extract audio link
                    audio_link = extract_audio_link(html_content, url)
                    if audio_link:
                        episode['audio_link'] = audio_link
                        processed_count += 1
                        
                        # Save immediately after finding each audio link
                        save_episodes_data(data)
                    else:
                        failed_count += 1
                else:
                    failed_count += 1
                
                # Update progress bar for each processed episode
                overall_pbar.update(1)
                
                # Be respectful with requests
                time.sleep(1)
    
        # Final summary
        print(f"\nCompleted audio link extraction!")
        print(f"  Successfully processed: {processed_count} episodes")
        print(f"  Skipped (already had audio): {skipped_count} episodes")
        print(f"  Failed to find audio: {failed_count} episodes")
        print(f"  Total episodes: {total_episodes}")
        
        # Final save
        save_episodes_data(data)
        print("Final data saved to episodes.json")

if __name__ == "__main__":
    main()