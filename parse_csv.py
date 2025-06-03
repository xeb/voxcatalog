#!/usr/bin/env python3
"""
Script to export Voxology podcast series and episode data to CSV format.
Combines data from series.json and episodes.json into a single CSV file.
"""

import json
import csv
import os
import sys
from datetime import datetime


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


def load_series_data():
    """Load series data from series.json."""
    try:
        with open('series.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: series.json not found. Run 'make series' first.")
        sys.exit(1)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading series.json: {e}")
        sys.exit(1)


def create_episode_lookup(episodes_data):
    """Create a lookup dictionary from file path to episode data."""
    episodes = episodes_data.get('episodes', [])
    lookup = {}
    
    for episode in episodes:
        file_path = episode.get('file_path')
        if file_path:
            lookup[file_path] = episode
    
    return lookup


def export_to_csv(series_data, episode_lookup, output_file='voxology_catalog.csv'):
    """Export series and episode data to CSV file."""
    
    print(f"📊 Exporting podcast catalog to {output_file}...")
    
    # Prepare CSV data
    csv_rows = []
    
    for series_name, episodes_in_series in series_data.items():
        if series_name == "INDEPENDENT":
            # Handle INDEPENDENT episodes (stored as list)
            if isinstance(episodes_in_series, list):
                for i, file_path in enumerate(episodes_in_series, 1):
                    episode_data = episode_lookup.get(file_path, {})
                    csv_rows.append({
                        'series_name': 'INDEPENDENT',
                        'episode_num': i,  # Sequential numbering for INDEPENDENT
                        'episode_date': episode_data.get('date', ''),
                        'episode_url': episode_data.get('url', ''),
                        'episode_file_path_mp3': file_path
                    })
            else:
                # Legacy dict format for INDEPENDENT
                for episode_num, file_path in episodes_in_series.items():
                    episode_data = episode_lookup.get(file_path, {})
                    csv_rows.append({
                        'series_name': 'INDEPENDENT',
                        'episode_num': episode_num,
                        'episode_date': episode_data.get('date', ''),
                        'episode_url': episode_data.get('url', ''),
                        'episode_file_path_mp3': file_path
                    })
        else:
            # Handle regular series (stored as numbered dict)
            for episode_num, file_path in episodes_in_series.items():
                episode_data = episode_lookup.get(file_path, {})
                csv_rows.append({
                    'series_name': series_name,
                    'episode_num': int(episode_num),
                    'episode_date': episode_data.get('date', ''),
                    'episode_url': episode_data.get('url', ''),
                    'episode_file_path_mp3': file_path
                })
    
    # Sort by series name, then by episode number
    csv_rows.sort(key=lambda x: (x['series_name'], x['episode_num']))
    
    # Write to CSV file
    fieldnames = ['series_name', 'episode_num', 'episode_date', 'episode_url', 'episode_file_path_mp3']
    
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_rows)
        
        print(f"✅ Successfully exported {len(csv_rows)} episodes to {output_file}")
        
        # Show summary statistics
        series_count = len(set(row['series_name'] for row in csv_rows))
        independent_count = len([row for row in csv_rows if row['series_name'] == 'INDEPENDENT'])
        series_episodes_count = len(csv_rows) - independent_count
        
        print(f"📊 Summary:")
        print(f"   📖 {series_count} total series (including INDEPENDENT)")
        print(f"   🎯 {independent_count} independent episodes")
        print(f"   📚 {series_episodes_count} episodes in {series_count - 1} named series")
        
        # Show episodes with missing data
        missing_dates = len([row for row in csv_rows if not row['episode_date']])
        missing_urls = len([row for row in csv_rows if not row['episode_url']])
        
        if missing_dates > 0:
            print(f"   ⚠️  {missing_dates} episodes missing dates")
        if missing_urls > 0:
            print(f"   ⚠️  {missing_urls} episodes missing URLs")
        
    except IOError as e:
        print(f"❌ Error writing CSV file: {e}")
        sys.exit(1)


def main():
    """Main function to export podcast data to CSV."""
    print("📁 Loading podcast data...")
    
    # Load data files
    episodes_data = load_episodes_data()
    series_data = load_series_data()
    
    # Create episode lookup
    episode_lookup = create_episode_lookup(episodes_data)
    
    print(f"📋 Loaded {len(episodes_data.get('episodes', []))} episodes and {len(series_data)} series")
    
    # Export to CSV
    export_to_csv(series_data, episode_lookup)
    
    print(f"\n💾 Export complete! Use the CSV file for:")
    print(f"   📈 Data analysis and visualization")
    print(f"   📊 Spreadsheet applications")
    print(f"   🔍 Episode discovery and organization")


if __name__ == "__main__":
    main()