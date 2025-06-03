#!/usr/bin/env python3
"""
Script to analyze Voxology podcast transcriptions and identify series patterns using Gemini AI.
Reads episodes.json, analyzes transcriptions, and builds series.json with structured data.
"""

import json
import os
import sys
from datetime import datetime
from tqdm import tqdm
from google import genai


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
    """Load existing series data from series.json if it exists."""
    if os.path.exists('series.json'):
        try:
            with open('series.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Error loading existing series.json: {e}")
            return {}
    return {}


def save_series_data(data):
    """Save series data to series.json."""
    try:
        with open('series.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"Error saving series.json: {e}")


def get_api_key():
    """Reads the Gemini API key from ~/.ssh/gemini_api_key.txt."""
    home_dir = os.path.expanduser("~")
    api_key_path = os.path.join(home_dir, ".ssh", "gemini_api_key.txt")
    
    try:
        with open(api_key_path, "r") as f:
            api_key = f.read().strip()
        return api_key
    except FileNotFoundError:
        print(f"Error: Gemini API key file not found at {api_key_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading API key: {e}")
        sys.exit(1)


def read_transcription_file(file_path):
    """Read and extract transcription text from a file."""
    if not file_path or not os.path.exists(file_path):
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract only the actual transcription text (skip headers and comments)
        transcription_lines = []
        for line in content.split('\n'):
            line = line.strip()
            # Skip empty lines, headers (starting with #), and section markers
            if line and not line.startswith('#') and not line.startswith('='):
                # Keep the full line including timestamps and speakers for context
                transcription_lines.append(line)
        
        return '\n'.join(transcription_lines)
    except Exception as e:
        print(f"Error reading transcription file {file_path}: {e}")
        return None


def analyze_episode_series(current_episode, previous_episode, existing_series, gemini_client):
    """Use Gemini to analyze if episodes are part of a series."""
    
    # Read transcriptions
    current_transcription = None
    previous_transcription = None
    
    # Try both local and AssemblyAI transcriptions for current episode
    if 'transcription_file_path' in current_episode:
        current_transcription = read_transcription_file(current_episode['transcription_file_path'])
    if not current_transcription and 'transcription_file_path_assemblyai' in current_episode:
        current_transcription = read_transcription_file(current_episode['transcription_file_path_assemblyai'])
    
    # Try both local and AssemblyAI transcriptions for previous episode
    if previous_episode:
        if 'transcription_file_path' in previous_episode:
            previous_transcription = read_transcription_file(previous_episode['transcription_file_path'])
        if not previous_transcription and 'transcription_file_path_assemblyai' in previous_episode:
            previous_transcription = read_transcription_file(previous_episode['transcription_file_path_assemblyai'])
    
    # Skip if no transcription available
    if not current_transcription:
        return None
    
    # Define the JSON schema for structured output
    json_schema = {
        "type": "object",
        "properties": {
            "series_name": {
                "type": "string",
                "description": "The name of the series this episode belongs to, or 'INDEPENDENT' if not part of a series"
            },
            "episode_number_in_series": {
                "type": "integer", 
                "description": "The episode number within the series, or 0 if INDEPENDENT"
            },
        },
        "required": ["series_name", "episode_number_in_series",]
    }
    
    # Build the prompt
    prompt = f"""You are analyzing podcast episode transcriptions to identify if episodes are part of a series or are independent episodes.

## CURRENT EPISODE METADATA:
- Title: {current_episode.get('title', 'Unknown')}
- URL: {current_episode.get('url', 'Unknown')}
- Page: {current_episode.get('page', 'Unknown')}

## CURRENT EPISODE TRANSCRIPTION:
{current_transcription[:8000]}  

## PREVIOUS EPISODE TRANSCRIPTION:
{previous_transcription[:8000] if previous_transcription else "No previous episode transcription available"}

## EXISTING SERIES DATA:
{json.dumps(existing_series, indent=2) if existing_series else "No existing series data"}

## INSTRUCTIONS:
1. Analyze the current episode transcription to determine if it's part of a series
2. Look for explicit indicators like:
   - "Part [number]" or "Episode [number]" in titles or content
   - References to previous episodes in the same series
   - Sequential topics or continuing themes
   - Explicit series names mentioned
3. Compare with the previous episode to see if there's a clear connection
4. Check existing series data to see if this fits into an established pattern

## IMPORTANT RULES:
- Only conclude an episode is part of a series if the transcription makes it EXPLICITLY clear
- Use "INDEPENDENT" as series_name if there's any doubt or if it's clearly a standalone episode
- Be conservative - err on the side of marking episodes as INDEPENDENT rather than forcing them into series
- Series names should be descriptive and based on content mentioned in the transcription
- Episode numbers should be sequential within each series (starting from 1)
- If you identify a new series, make sure the episode_number_in_series starts at 1

Analyze the transcription evidence and provide your assessment."""

    try:
        # Generate the response using Gemini with structured output
        response = gemini_client.models.generate_content(
            model='gemini-2.5-pro-preview-05-06',
            contents=prompt,
            config={
                'response_mime_type': 'application/json',
                'response_schema': json_schema
            }
        )
        
        # Parse the JSON from the response
        try:
            structured_data = response.text
            result = json.loads(structured_data)
            return result
        except Exception as e:
            print(f"Error parsing Gemini response: {e}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return None


def get_episode_file_path(episode):
    """Get the file path for an episode (prefer audio files)."""
    # Return the audio file path if available
    if 'file_path' in episode and episode['file_path']:
        return episode['file_path']
    
    # Fallback to URL if no file path
    return episode.get('url', 'Unknown')


def is_episode_already_processed(episode, series_data):
    """Check if an episode is already processed in series_data."""
    episode_file_path = get_episode_file_path(episode)
    
    # Search through all series to see if this episode file path exists
    for series_name, episodes_in_series in series_data.items():
        if series_name == "INDEPENDENT":
            # Handle INDEPENDENT as either a list or dict (for backward compatibility)
            if isinstance(episodes_in_series, list):
                if episode_file_path in episodes_in_series:
                    return True, series_name, 0  # INDEPENDENT episodes don't have episode numbers
            elif isinstance(episodes_in_series, dict):
                # Legacy format - convert to list
                for episode_num, file_path in episodes_in_series.items():
                    if file_path == episode_file_path:
                        return True, series_name, 0
        else:
            # Regular series with episode numbers
            for episode_num, file_path in episodes_in_series.items():
                if file_path == episode_file_path:
                    return True, series_name, int(episode_num)
    
    return False, None, None


def main():
    """Main function to analyze episodes and build series data."""
    print("🔍 Starting series analysis process...")
    
    # Load episode data
    print("📂 Loading episode data...")
    episodes_data = load_episodes_data()
    episodes = episodes_data.get('episodes', [])
    
    if not episodes:
        print("No episodes found in episodes.json")
        return
    
    # Load existing series data
    print("📚 Loading existing series data...")
    series_data = load_series_data()
    
    # Migrate INDEPENDENT from old dict format to new list format
    if "INDEPENDENT" in series_data and isinstance(series_data["INDEPENDENT"], dict):
        print("🔄 Migrating INDEPENDENT episodes from dict to list format...")
        old_independent = series_data["INDEPENDENT"]
        series_data["INDEPENDENT"] = list(old_independent.values())
        save_series_data(series_data)
        print(f"✅ Migrated {len(series_data['INDEPENDENT'])} INDEPENDENT episodes")
    
    # Initialize Gemini client
    print("🤖 Initializing Gemini AI client...")
    api_key = get_api_key()
    gemini_client = genai.Client(api_key=api_key, http_options={'api_version': 'v1alpha'})
    print("✅ Gemini client initialized")
    
    # Filter episodes that have transcriptions
    episodes_with_transcriptions = []
    for episode in episodes:
        has_local = 'transcription_file_path' in episode and episode['transcription_file_path'] and os.path.exists(episode['transcription_file_path'])
        has_assemblyai = 'transcription_file_path_assemblyai' in episode and episode['transcription_file_path_assemblyai'] and os.path.exists(episode['transcription_file_path_assemblyai'])
        if has_local or has_assemblyai:
            episodes_with_transcriptions.append(episode)
    
    if not episodes_with_transcriptions:
        print("No episodes with transcriptions found. Run transcription first.")
        return
    
    # Sort episodes by page number for proper sequence
    episodes_with_transcriptions.sort(key=lambda x: x.get('page', 0))
    
    print(f"\n🎙️ Found {len(episodes_with_transcriptions)} episodes with transcriptions")
    print(f"📊 Processing episodes in sequence...")
    
    # Track statistics
    processed_count = 0
    series_count = 0
    independent_count = 0
    failed_count = 0
    
    # Process each episode
    with tqdm(
        total=len(episodes_with_transcriptions),
        desc="🔍 Series Analysis",
        unit="episodes",
        ncols=100
    ) as pbar:
        
        for i, current_episode in enumerate(episodes_with_transcriptions):
            title = current_episode.get('title', 'Unknown')
            
            # Check if episode is already processed
            already_processed, existing_series, existing_episode_num = is_episode_already_processed(current_episode, series_data)
            
            if already_processed:
                # Episode already processed, skip Gemini analysis
                series_name = existing_series
                episode_num = existing_episode_num
                
                # Update statistics
                if series_name == "INDEPENDENT":
                    independent_count += 1
                else:
                    series_count += 1
                
                processed_count += 1
                
                # Update progress description
                if series_name != "INDEPENDENT":
                    pbar.set_postfix_str(f"Cached: {series_name[:15]}... (ep {episode_num})")
                else:
                    pbar.set_postfix_str(f"Cached: Independent")
            else:
                # Episode not processed yet, analyze with Gemini
                # Get previous episode (if exists)
                previous_episode = episodes_with_transcriptions[i-1] if i > 0 else None
                
                # Analyze series with Gemini
                analysis = analyze_episode_series(
                    current_episode, 
                    previous_episode, 
                    series_data,
                    gemini_client
                )
                
                if analysis:
                    series_name = analysis['series_name']
                    episode_num = analysis['episode_number_in_series']
                    episode_file_path = get_episode_file_path(current_episode)
                    
                    # Add debug for new series discovery
                    if series_name not in series_data:
                        if series_name == "INDEPENDENT":
                            print(f"🔍 DEBUG: New INDEPENDENT episode: {episode_file_path}")
                        else:
                            print(f"🔍 DEBUG: New series discovered: '{series_name}' starting with episode {episode_num}")
                    
                    # Handle INDEPENDENT episodes as a simple list
                    if series_name == "INDEPENDENT":
                        if series_name not in series_data:
                            series_data[series_name] = []
                        series_data[series_name].append(episode_file_path)
                    else:
                        # Regular series with episode numbers
                        if series_name not in series_data:
                            series_data[series_name] = {}
                        series_data[series_name][str(episode_num)] = episode_file_path
                    
                    # Save progress immediately
                    save_series_data(series_data)
                    
                    # Update statistics
                    if series_name == "INDEPENDENT":
                        independent_count += 1
                    else:
                        series_count += 1
                    
                    processed_count += 1
                    
                    # Update progress description
                    if series_name != "INDEPENDENT":
                        pbar.set_postfix_str(f"New: {series_name[:20]}... (ep {episode_num})")
                    else:
                        pbar.set_postfix_str(f"New: Independent")
                else:
                    failed_count += 1
                    pbar.set_postfix_str(f"Analysis failed")
            
            pbar.update(1)
    
    # Final summary
    print(f"\n🎉 Series analysis complete!")
    print(f"  ✅ Successfully processed: {processed_count} episodes")
    print(f"  📚 Episodes in series: {series_count}")
    print(f"  🎯 Independent episodes: {independent_count}")
    print(f"  ❌ Failed analyses: {failed_count}")
    
    # Show series summary
    if series_data:
        series_list = [name for name in series_data.keys() if name != "INDEPENDENT"]
        if series_list:
            print(f"\n📚 IDENTIFIED SERIES:")
            for series_name in sorted(series_list):
                episode_count = len(series_data[series_name])
                print(f"  📖 {series_name}: {episode_count} episodes")
        
        if "INDEPENDENT" in series_data:
            independent_ep_count = len(series_data["INDEPENDENT"])
            print(f"  🎯 Independent episodes: {independent_ep_count}")
    
    # Final save
    save_series_data(series_data)
    print(f"\n💾 Series data saved to series.json")


if __name__ == "__main__":
    main()
