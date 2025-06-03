#!/usr/bin/env python3
"""
Script to download audio files from Voxology podcast episodes.
Reads episodes.json and downloads audio files to the catalog directory.
"""

import requests
import json
import os
import time
from datetime import datetime
import sys
from urllib.parse import urlparse
from collections import defaultdict
import re
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

def create_catalog_directory():
    """Create the catalog directory if it doesn't exist."""
    if not os.path.exists('catalog'):
        os.makedirs('catalog')
        print("Created catalog directory")

def generate_filename_from_url(episode_url, audio_url):
    """Generate filename based on the episode URL path."""
    # Parse the episode URL to get the path
    parsed_url = urlparse(episode_url)
    episode_path = parsed_url.path.strip('/')
    
    # Remove common prefixes and clean up the path
    if episode_path.startswith('episodes/'):
        episode_path = episode_path[9:]  # Remove 'episodes/' prefix
    
    # Parse the audio URL to get the file extension
    audio_parsed = urlparse(audio_url)
    audio_filename = os.path.basename(audio_parsed.path)
    
    # Get file extension from audio URL
    if '.' in audio_filename:
        extension = '.' + audio_filename.split('.')[-1]
    else:
        extension = '.mp3'  # Default to mp3 if no extension found
    
    # Clean up the episode path for use as filename
    # Replace slashes with underscores and remove invalid characters
    safe_filename = re.sub(r'[^\w\-_.]', '_', episode_path)
    safe_filename = re.sub(r'_+', '_', safe_filename)  # Replace multiple underscores with single
    safe_filename = safe_filename.strip('_')  # Remove leading/trailing underscores
    
    # Add extension if not already present
    if not safe_filename.endswith(extension):
        safe_filename += extension
    
    return safe_filename

def download_file(url, filepath, episode_title):
    """Download a file from URL to filepath silently."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Stream the download to handle large files
        response = requests.get(url, headers=headers, stream=True, timeout=30)
        response.raise_for_status()
        
        # Download without progress bar (silent)
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        return True
        
    except requests.RequestException:
        # Clean up partial file
        if os.path.exists(filepath):
            os.remove(filepath)
        return False
    except Exception:
        # Clean up partial file
        if os.path.exists(filepath):
            os.remove(filepath)
        return False

def group_episodes_by_page(episodes):
    """Group episodes by page number for batch processing."""
    pages = defaultdict(list)
    for episode in episodes:
        pages[episode['page']].append(episode)
    return pages

def main():
    """Main function to download audio files for all episodes."""
    print("Starting audio file download process...")
    
    # Load episode data
    data = load_episodes_data()
    episodes = data.get('episodes', [])
    
    if not episodes:
        print("No episodes found in episodes.json")
        return
    
    # Create catalog directory
    create_catalog_directory()
    
    # Filter episodes that have audio links
    episodes_with_audio = [ep for ep in episodes if 'audio_link' in ep and ep['audio_link']]
    episodes_without_audio = [ep for ep in episodes if 'audio_link' not in ep or not ep['audio_link']]
    
    if episodes_without_audio:
        print(f"\n⚠️  {len(episodes_without_audio)} episodes don't have audio links yet.")
        print("Run 'make audiolinks' first to get audio links for all episodes.")
    
    if not episodes_with_audio:
        print("No episodes with audio links found. Run get_episode_audio_links.py first.")
        return
    
    # Group episodes by page for organized processing
    pages = group_episodes_by_page(episodes_with_audio)
    total_pages = len(pages)
    total_episodes = len(episodes_with_audio)
    
    print(f"\nFound {total_episodes} episodes with audio links across {total_pages} pages")
    
    # Track progress
    downloaded_count = 0
    skipped_count = 0
    failed_count = 0
    
    # Create overall progress bar for file downloads
    with tqdm(
        total=total_episodes,
        desc="💾 Downloads Progress",
        unit="files",
        ncols=100,
        position=0
    ) as overall_pbar:
        
        # Process each page as a batch
        for page_num in sorted(pages.keys()):
            page_episodes = pages[page_num]
            
            print(f"\n📁 Processing page {page_num} ({len(page_episodes)} episodes)...")
            
            # Check which episodes already have files downloaded and which need them
            episodes_with_files = [ep for ep in page_episodes if 'file_path' in ep and ep['file_path'] and os.path.exists(ep['file_path'])]
            episodes_needing_files = [ep for ep in page_episodes if 'file_path' not in ep or not ep['file_path'] or not os.path.exists(ep.get('file_path', ''))]
            
            # Show episodes that already have files downloaded (skipped)
            if episodes_with_files:
                print(f"  Files already downloaded ({len(episodes_with_files)}):")
                for episode in episodes_with_files:
                    title = episode.get('title', 'Unknown')
                    filename = os.path.basename(episode['file_path'])
                    print(f"    ✅ {title} → {filename}")
                    overall_pbar.update(1)  # Update progress bar for skipped files
                skipped_count += len(episodes_with_files)
            
            if not episodes_needing_files:
                print(f"  All files on page {page_num} already downloaded, moving to next page...")
                continue
            
            # Show episodes that need file downloads
            print(f"  Files to download ({len(episodes_needing_files)}):")
            for episode in episodes_needing_files:
                title = episode.get('title', 'Unknown')
                print(f"    ⚪ {title}")
            
            # Download files for episodes that need them
            for episode in episodes_needing_files:
                url = episode['url']
                audio_url = episode['audio_link']
                title = episode.get('title', 'Unknown')
                
                # Generate filename from episode URL
                filename = generate_filename_from_url(url, audio_url)
                filepath = os.path.join('catalog', filename)
                
                # Check if file already exists
                if os.path.exists(filepath):
                    # Update the JSON record even if file exists
                    episode['file_path'] = filepath
                    save_episodes_data(data)
                    skipped_count += 1
                    overall_pbar.update(1)  # Update progress bar
                    continue
                
                # Download the file
                download_success = download_file(audio_url, filepath, title)
                
                # Always update JSON record if file exists after download attempt
                if os.path.exists(filepath):
                    episode['file_path'] = filepath
                    save_episodes_data(data)
                    
                    if download_success:
                        downloaded_count += 1
                    else:
                        # File exists but download reported failure - still count as success
                        downloaded_count += 1
                else:
                    failed_count += 1
                
                # Update progress bar for each processed file
                overall_pbar.update(1)
                
                # Be respectful with requests
                time.sleep(2)
    
        # Final summary
        print(f"\n🎉 Completed audio file download process!")
        print(f"  ✅ Successfully downloaded: {downloaded_count} files")
        print(f"  ⏭️  Skipped (already existed): {skipped_count} files")
        print(f"  ❌ Failed downloads: {failed_count} files")
        print(f"  📊 Total episodes processed: {total_episodes}")
        
        # Final save
        save_episodes_data(data)
        print(f"\n💾 Final data saved to episodes.json")
        print(f"📁 Audio files saved in: ./catalog/")

if __name__ == "__main__":
    main()