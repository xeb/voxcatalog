#!/usr/bin/env python3
"""
Script to transcribe audio files from Voxology podcast episodes using OpenAI Whisper and pyannote.audio.
Reads episodes.json and transcribes audio files to text with speaker diarization.
"""

import warnings
# Suppress common warnings for cleaner output
warnings.filterwarnings("ignore", category=UserWarning, module="torchaudio")
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pyannote")
warnings.filterwarnings("ignore", category=UserWarning, module="pyannote")
warnings.filterwarnings("ignore", message=".*MPEG_LAYER_III.*")
warnings.filterwarnings("ignore", message=".*invalid escape sequence.*")
warnings.filterwarnings("ignore", message=".*TensorFloat-32.*")
warnings.filterwarnings("ignore", message=".*std\\(\\): degrees of freedom.*")
warnings.filterwarnings("ignore", message=".*reproducibility.*")

# Also suppress specific warning categories
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
try:
    from pyannote.audio.utils.reproducibility import ReproducibilityWarning
    warnings.filterwarnings("ignore", category=ReproducibilityWarning)
except ImportError:
    pass

import whisper
import json
import os
import sys
import time
from datetime import datetime
from collections import defaultdict
from tqdm import tqdm
from pyannote.audio import Pipeline
import torch


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


def load_huggingface_token():
    """Load HuggingFace token from ~/.huggingface/token.txt."""
    token_path = os.path.expanduser("~/.huggingface/token.txt")
    try:
        with open(token_path, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Error: HuggingFace token not found at {token_path}")
        print("Please save your HuggingFace token to ~/.huggingface/token.txt")
        sys.exit(1)
    except IOError as e:
        print(f"Error reading HuggingFace token: {e}")
        sys.exit(1)


def initialize_models():
    """Initialize Whisper and pyannote models."""
    print("🔧 Initializing transcription models...")
    
    # Load Whisper base model for English
    print("  📥 Loading Whisper base model...")
    try:
        whisper_model = whisper.load_model("base")
        print("  ✅ Whisper model loaded successfully")
    except Exception as e:
        print(f"  ❌ Error loading Whisper model: {e}")
        sys.exit(1)
    
    # Load HuggingFace token and initialize pyannote pipeline
    print("  🔐 Loading HuggingFace authentication...")
    hf_token = load_huggingface_token()
    print("  ✅ HuggingFace token loaded")
    
    print("  📥 Loading pyannote.audio speaker diarization pipeline...")
    print("     This may take a few minutes on first run...")
    
    try:
        # Initialize speaker diarization pipeline
        diarization_pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=hf_token
        )
        print("  ✅ Diarization pipeline loaded successfully")
        
        # Use GPU if available
        device = "cuda" if torch.cuda.is_available() else "cpu"
        if device == "cuda":
            diarization_pipeline = diarization_pipeline.to(torch.device("cuda"))
            print("  🚀 Using GPU for speaker diarization")
        else:
            print("  💻 Using CPU for speaker diarization")
        
        print("🎉 All models initialized successfully!")
        return whisper_model, diarization_pipeline
        
    except Exception as e:
        print(f"  ❌ Error loading pyannote diarization pipeline: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Visit https://hf.co/pyannote/speaker-diarization-3.1 and accept user conditions")
        print("   2. Visit https://hf.co/pyannote/segmentation-3.0 and accept user conditions") 
        print("   3. Visit https://hf.co/pyannote/wespeaker-voxceleb-resnet34-LM and accept user conditions")
        print("   4. Ensure your HuggingFace token has the required permissions")
        print("   5. Check that ~/.huggingface/token.txt contains a valid token")
        print("\n💡 You can also run without speaker diarization by modifying the script")
        sys.exit(1)


def transcribe_audio_file(audio_path, whisper_model, diarization_pipeline, episode_title):
    """Transcribe audio file with speaker diarization."""
    try:
        start_time = time.time()
        
        # First, get speaker diarization
        print(f"      🎭 Performing speaker diarization... (this may take several minutes)")
        diarization_start = time.time()
        diarization = diarization_pipeline(audio_path)
        diarization_time = time.time() - diarization_start
        print(f"      ✅ Speaker diarization complete ({diarization_time:.1f}s)")
        
        # Transcribe with Whisper
        print(f"      🎤 Transcribing audio with Whisper... (this may take several minutes)")
        whisper_start = time.time()
        result = whisper_model.transcribe(audio_path, language="en")
        whisper_time = time.time() - whisper_start
        print(f"      ✅ Whisper transcription complete ({whisper_time:.1f}s)")
        
        # Combine transcription with speaker information
        print(f"      🔄 Processing and combining transcription with speaker data...")
        transcription_lines = []
        transcription_lines.append(f"# Transcription: {episode_title}")
        transcription_lines.append(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        transcription_lines.append(f"# Audio file: {os.path.basename(audio_path)}")
        transcription_lines.append("")
        
        # Get segments from Whisper
        segments = result.get("segments", [])
        
        # Create speaker-aware transcription
        for segment in segments:
            start_time = segment["start"]
            end_time = segment["end"]
            text = segment["text"].strip()
            
            # Find speaker for this time segment
            speaker = "UNKNOWN"
            for turn, track, speaker_label in diarization.itertracks(yield_label=True):
                if (start_time >= turn.start and start_time <= turn.end) or \
                   (end_time >= turn.start and end_time <= turn.end) or \
                   (start_time <= turn.start and end_time >= turn.end):
                    speaker = speaker_label
                    break
            
            # Format timestamp
            start_min = int(start_time // 60)
            start_sec = int(start_time % 60)
            end_min = int(end_time // 60)
            end_sec = int(end_time % 60)
            
            timestamp = f"[{start_min:02d}:{start_sec:02d} - {end_min:02d}:{end_sec:02d}]"
            
            transcription_lines.append(f"{timestamp} {speaker}: {text}")
        
        # Also add full text without speakers for easier reading
        transcription_lines.append("")
        transcription_lines.append("# Full Transcription (without speaker labels)")
        transcription_lines.append("")
        transcription_lines.append(result.get("text", ""))
        
        total_time = time.time() - start_time
        print(f"      ✅ Transcription processing complete (total: {total_time:.1f}s)")
        return "\n".join(transcription_lines)
        
    except Exception as e:
        print(f"Error transcribing {audio_path}: {e}")
        return None


def group_episodes_by_page(episodes):
    """Group episodes by page number for batch processing."""
    pages = defaultdict(list)
    for episode in episodes:
        pages[episode['page']].append(episode)
    return pages


def main():
    """Main function to transcribe audio files for all episodes."""
    print("🎙️  Starting audio transcription process...")
    
    # Load episode data
    print("📂 Loading episode data...")
    data = load_episodes_data()
    episodes = data.get('episodes', [])
    
    if not episodes:
        print("No episodes found in episodes.json")
        return
    
    # Initialize models
    whisper_model, diarization_pipeline = initialize_models()
    
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
        desc="🎙️  Transcription Progress",
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
                # Generate expected transcription path
                audio_filename = os.path.basename(episode['file_path'])
                transcript_filename = os.path.splitext(audio_filename)[0] + '.txt'
                expected_transcript_path = os.path.join('catalog', transcript_filename)
                
                # Check if JSON has correct transcription path
                has_correct_json_path = ('transcription_file_path' in episode and 
                                       episode['transcription_file_path'] == expected_transcript_path)
                
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
                    filename = os.path.basename(episode['transcription_file_path'])
                    print(f"    ✅ {title} → {filename}")
                    overall_pbar.update(1)  # Update progress bar for skipped files
                skipped_count += len(episodes_with_transcriptions)
            
            # Handle episodes where transcription exists but JSON needs updating
            if episodes_json_update_needed:
                print(f"  JSON updates needed ({len(episodes_json_update_needed)}):") 
                for episode in episodes_json_update_needed:
                    title = episode.get('title', 'Unknown')
                    audio_filename = os.path.basename(episode['file_path'])
                    transcript_filename = os.path.splitext(audio_filename)[0] + '.txt'
                    expected_transcript_path = os.path.join('catalog', transcript_filename)
                    
                    # Update JSON record with correct path
                    episode['transcription_file_path'] = expected_transcript_path
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
                
                # Generate transcription filename from audio filename
                audio_filename = os.path.basename(audio_path)
                transcript_filename = os.path.splitext(audio_filename)[0] + '.txt'
                transcript_path = os.path.join('catalog', transcript_filename)
                
                # Check if transcription file already exists
                if os.path.exists(transcript_path):
                    # Update the JSON record even if file exists
                    episode['transcription_file_path'] = transcript_path
                    save_episodes_data(data)
                    skipped_count += 1
                    overall_pbar.update(1)  # Update progress bar
                    continue
                
                print(f"\n  🎙️  Transcribing: {title}")
                print(f"      Audio: {audio_path}")
                print(f"      Output: {transcript_path}")
                
                # Transcribe the file
                transcription = transcribe_audio_file(audio_path, whisper_model, diarization_pipeline, title)
                
                if transcription:
                    # Save transcription to file
                    try:
                        with open(transcript_path, 'w', encoding='utf-8') as f:
                            f.write(transcription)
                        
                        # Update JSON record
                        episode['transcription_file_path'] = transcript_path
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
        
        # Final summary
        print(f"\n🎉 Completed audio transcription process!")
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