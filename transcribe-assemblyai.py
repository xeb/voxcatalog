#!/usr/bin/env python3
"""
Script to transcribe audio files from Voxology podcast episodes using AssemblyAI.
Reads episodes.json and transcribes audio files to text with speaker diarization.
"""

import json
import os
import sys
import time
from datetime import datetime
from collections import defaultdict
from tqdm import tqdm
import assemblyai as aai


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


def load_assemblyai_api_key():
    """Load AssemblyAI API key from ~/.ssh/assemblyai.txt."""
    api_key_path = os.path.expanduser("~/.ssh/assemblyai.txt")
    try:
        with open(api_key_path, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Error: AssemblyAI API key not found at {api_key_path}")
        print("Please save your AssemblyAI API key to ~/.ssh/assemblyai.txt")
        sys.exit(1)
    except IOError as e:
        print(f"Error reading AssemblyAI API key: {e}")
        sys.exit(1)


def initialize_assemblyai():
    """Initialize AssemblyAI with API key."""
    print("🔧 Initializing AssemblyAI...")
    
    # Load API key
    print("  🔐 Loading AssemblyAI API key...")
    api_key = load_assemblyai_api_key()
    aai.settings.api_key = api_key
    print("  ✅ AssemblyAI API key loaded")
    
    # Create transcriber configuration
    print("  ⚙️  Configuring transcription settings...")
    config = aai.TranscriptionConfig(
        speaker_labels=True,
        language_code="en",
        auto_highlights=True,
        punctuate=True,
        format_text=True
    )
    
    transcriber = aai.Transcriber()
    print("🎉 AssemblyAI initialized successfully!")
    return transcriber, config


def transcribe_audio_file(audio_path, transcriber, config, episode_title):
    """Transcribe audio file with AssemblyAI speaker diarization."""
    try:
        start_time = time.time()
        
        print(f"      🚀 Uploading and transcribing with AssemblyAI...")
        print(f"      📤 This will upload the file and process remotely...")
        
        # Start transcription
        transcription_start = time.time()
        transcript = transcriber.transcribe(audio_path, config)
        transcription_time = time.time() - transcription_start
        
        # Check if transcription was successful
        if transcript.status == aai.TranscriptStatus.error:
            print(f"      ❌ AssemblyAI transcription failed: {transcript.error}")
            return None
        
        print(f"      ✅ AssemblyAI transcription complete ({transcription_time:.1f}s)")
        
        # Format the transcription
        print(f"      🔄 Processing and formatting transcription...")
        transcription_lines = []
        transcription_lines.append(f"# Transcription: {episode_title}")
        transcription_lines.append(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        transcription_lines.append(f"# Audio file: {os.path.basename(audio_path)}")
        transcription_lines.append(f"# Service: AssemblyAI")
        transcription_lines.append("")
        
        # Add speaker-labeled utterances
        if transcript.utterances:
            transcription_lines.append("# Speaker-labeled Transcription")
            transcription_lines.append("")
            
            for utterance in transcript.utterances:
                # Convert milliseconds to seconds for timestamp
                start_seconds = utterance.start / 1000
                end_seconds = utterance.end / 1000
                
                # Format timestamp
                start_min = int(start_seconds // 60)
                start_sec = int(start_seconds % 60)
                end_min = int(end_seconds // 60)
                end_sec = int(end_seconds % 60)
                
                timestamp = f"[{start_min:02d}:{start_sec:02d} - {end_min:02d}:{end_sec:02d}]"
                speaker = f"SPEAKER_{utterance.speaker}"
                
                transcription_lines.append(f"{timestamp} {speaker}: {utterance.text}")
        
        total_time = time.time() - start_time
        print(f"      ✅ Transcription processing complete (total: {total_time:.1f}s)")
        return "\n".join(transcription_lines)
        
    except Exception as e:
        print(f"      ❌ Error transcribing {audio_path}: {e}")
        return None


def group_episodes_by_page(episodes):
    """Group episodes by page number for batch processing."""
    pages = defaultdict(list)
    for episode in episodes:
        pages[episode['page']].append(episode)
    return pages


def main():
    """Main function to transcribe audio files for all episodes."""
    print("🎙️  Starting AssemblyAI transcription process...")
    
    # Load episode data
    print("📂 Loading episode data...")
    data = load_episodes_data()
    episodes = data.get('episodes', [])
    
    if not episodes:
        print("No episodes found in episodes.json")
        return
    
    # Initialize AssemblyAI
    transcriber, config = initialize_assemblyai()
    
    # Filter episodes that have audio files downloaded
    episodes_with_files = [ep for ep in episodes if 'file_path' in ep and ep['file_path'] and os.path.exists(ep['file_path'])]
    episodes_without_files = [ep for ep in episodes if 'file_path' not in ep or not ep['file_path'] or not os.path.exists(ep.get('file_path', ''))]
    
    if episodes_without_files:
        print(f"\n⚠️  {len(episodes_without_files)} episodes don't have audio files yet.")
        print("Run 'make download' first to download audio files for all episodes.")
    
    if not episodes_with_files:
        print("No episodes with audio files found. Run get_audio_files.py first.")
        return
    
    # Group episodes by page for organized processing
    pages = group_episodes_by_page(episodes_with_files)
    total_pages = len(pages)
    total_episodes = len(episodes_with_files)
    
    print(f"\nFound {total_episodes} episodes with audio files across {total_pages} pages")
    
    # Track progress
    transcribed_count = 0
    skipped_count = 0
    failed_count = 0
    
    # Create overall progress bar for transcriptions
    with tqdm(
        total=total_episodes,
        desc="🎙️  AssemblyAI Progress",
        unit="files",
        ncols=100,
        position=0
    ) as overall_pbar:
        
        # Process each page as a batch
        for page_num in sorted(pages.keys()):
            page_episodes = pages[page_num]
            
            print(f"\n📁 Processing page {page_num} ({len(page_episodes)} episodes)...")
            
            # Check transcription status for each episode
            episodes_with_transcriptions = []
            episodes_needing_transcriptions = []
            episodes_json_update_needed = []
            
            for episode in page_episodes:
                # Generate expected transcription path with assemblyai suffix
                audio_filename = os.path.basename(episode['file_path'])
                transcript_filename = os.path.splitext(audio_filename)[0] + '-assemblyai.txt'
                expected_transcript_path = os.path.join('catalog', transcript_filename)
                
                # Check if JSON has correct transcription path
                has_correct_json_path = ('transcription_file_path_assemblyai' in episode and 
                                       episode['transcription_file_path_assemblyai'] == expected_transcript_path)
                
                # Check if transcription file actually exists
                transcript_exists = os.path.exists(expected_transcript_path)
                
                if transcript_exists and has_correct_json_path:
                    # File exists and JSON is up to date
                    episodes_with_transcriptions.append(episode)
                elif transcript_exists and not has_correct_json_path:
                    # File exists but JSON needs updating
                    episodes_json_update_needed.append(episode)
                else:
                    # File doesn't exist, needs transcription
                    episodes_needing_transcriptions.append(episode)
            
            # Show episodes that already have transcriptions (skipped)
            if episodes_with_transcriptions:
                print(f"  Transcriptions already completed ({len(episodes_with_transcriptions)}):") 
                for episode in episodes_with_transcriptions:
                    title = episode.get('title', 'Unknown')
                    filename = os.path.basename(episode['transcription_file_path_assemblyai'])
                    print(f"    ✅ {title} → {filename}")
                    overall_pbar.update(1)  # Update progress bar for skipped files
                skipped_count += len(episodes_with_transcriptions)
            
            # Handle episodes where transcription exists but JSON needs updating
            if episodes_json_update_needed:
                print(f"  JSON updates needed ({len(episodes_json_update_needed)}):") 
                for episode in episodes_json_update_needed:
                    title = episode.get('title', 'Unknown')
                    audio_filename = os.path.basename(episode['file_path'])
                    transcript_filename = os.path.splitext(audio_filename)[0] + '-assemblyai.txt'
                    expected_transcript_path = os.path.join('catalog', transcript_filename)
                    
                    # Update JSON record with correct path
                    episode['transcription_file_path_assemblyai'] = expected_transcript_path
                    print(f"    🔄 {title} → {transcript_filename}")
                    overall_pbar.update(1)  # Update progress bar
                    
                # Save JSON updates immediately
                save_episodes_data(data)
                skipped_count += len(episodes_json_update_needed)
            
            if not episodes_needing_transcriptions:
                print(f"  All transcriptions on page {page_num} already completed, moving to next page...")
                continue
            
            # Show episodes that need transcriptions
            print(f"  Transcriptions to process ({len(episodes_needing_transcriptions)}):") 
            for episode in episodes_needing_transcriptions:
                title = episode.get('title', 'Unknown')
                print(f"    🎙️  {title}")
            
            # Transcribe files for episodes that need them
            for episode in episodes_needing_transcriptions:
                url = episode['url']
                audio_path = episode['file_path']
                title = episode.get('title', 'Unknown')
                
                # Generate transcription filename with assemblyai suffix
                audio_filename = os.path.basename(audio_path)
                transcript_filename = os.path.splitext(audio_filename)[0] + '-assemblyai.txt'
                transcript_path = os.path.join('catalog', transcript_filename)
                
                # Check if transcription file already exists
                if os.path.exists(transcript_path):
                    # Update the JSON record even if file exists
                    episode['transcription_file_path_assemblyai'] = transcript_path
                    save_episodes_data(data)
                    skipped_count += 1
                    overall_pbar.update(1)  # Update progress bar
                    continue
                
                print(f"\n  🎙️  Transcribing: {title}")
                print(f"      Audio: {audio_path}")
                print(f"      Output: {transcript_path}")
                
                # Transcribe the file
                transcription = transcribe_audio_file(audio_path, transcriber, config, title)
                
                if transcription:
                    # Save transcription to file
                    try:
                        with open(transcript_path, 'w', encoding='utf-8') as f:
                            f.write(transcription)
                        
                        # Update JSON record
                        episode['transcription_file_path_assemblyai'] = transcript_path
                        save_episodes_data(data)
                        transcribed_count += 1
                        print(f"      ✅ Transcription saved to {transcript_path}")
                        
                    except IOError as e:
                        print(f"      ❌ Error saving transcription: {e}")
                        failed_count += 1
                else:
                    failed_count += 1
                    print(f"      ❌ Transcription failed")
                
                # Update progress bar for each processed file
                overall_pbar.update(1)
                
                # Be respectful with API requests (AssemblyAI has rate limits)
                time.sleep(1)
        
        # Final summary
        print(f"\n🎉 Completed AssemblyAI transcription process!")
        print(f"  ✅ Successfully transcribed: {transcribed_count} files")
        print(f"  ⏭️  Skipped (already existed): {skipped_count} files")
        print(f"  ❌ Failed transcriptions: {failed_count} files")
        print(f"  📊 Total episodes processed: {total_episodes}")
        
        # Final save
        save_episodes_data(data)
        print(f"\n💾 Final data saved to episodes.json")
        print(f"📁 Transcription files saved in: ./catalog/")


if __name__ == "__main__":
    main()