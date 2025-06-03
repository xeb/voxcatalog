#!/usr/bin/env python3
"""
Script to analyze audio file statistics from Voxology podcast episodes.
Uses ffmpeg to get duration and file size information for all MP3/M4A files.
"""

import json
import os
import sys
from datetime import datetime
from tqdm import tqdm
import subprocess


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
    """Load series data from series.json if it exists."""
    if os.path.exists('series.json'):
        try:
            with open('series.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Error loading series.json: {e}")
            return {}
    return {}


def save_episodes_data(data):
    """Save updated episode data back to episodes.json."""
    data["last_updated"] = datetime.now().isoformat()
    try:
        with open('episodes.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"Error saving episodes.json: {e}")


def get_audio_info(file_path, episode_data=None):
    """Get duration and file size for an audio file, using cached values if available."""
    try:
        # Get file size in bytes
        file_size = os.path.getsize(file_path)
        
        # Check if we have cached audio metadata
        if episode_data and 'audio_metadata' in episode_data:
            metadata = episode_data['audio_metadata']
            cached_file_size = metadata.get('file_size_bytes', 0)
            cached_duration = metadata.get('duration_seconds', 0)
            
            # Use cached values if file size matches (file hasn't changed)
            if cached_file_size == file_size and cached_duration > 0:
                return {
                    'duration_seconds': cached_duration,
                    'file_size_bytes': file_size,
                    'success': True,
                    'cached': True
                }
        
        # Use ffprobe to get duration if not cached or file changed
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-show_entries', 'format=duration',
            '-of', 'csv=p=0',
            file_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and result.stdout.strip():
            duration = float(result.stdout.strip())
            return {
                'duration_seconds': duration,
                'file_size_bytes': file_size,
                'success': True,
                'cached': False
            }
        else:
            # Provide detailed error information
            error_msg = f"ffprobe failed (exit code {result.returncode})"
            if result.stderr:
                stderr_text = result.stderr.strip()
                error_msg += f" - stderr: {stderr_text}"
                
                # Check for common issues and provide helpful explanations
                if "moov atom not found" in stderr_text:
                    error_msg += " [ISSUE: Corrupted/incomplete M4A file - missing metadata]"
                elif "Invalid data found when processing input" in stderr_text:
                    error_msg += " [ISSUE: File appears to be corrupted or incomplete]"
                elif "No such file or directory" in stderr_text:
                    error_msg += " [ISSUE: File not found]"
                    
            if result.stdout:
                error_msg += f" - stdout: {result.stdout.strip()}"
            else:
                error_msg += " - no output"
            
            return {
                'duration_seconds': 0,
                'file_size_bytes': file_size,
                'success': False,
                'cached': False,
                'error': error_msg
            }
    
    except subprocess.TimeoutExpired:
        return {
            'duration_seconds': 0,
            'file_size_bytes': 0,
            'success': False,
            'cached': False,
            'error': 'ffprobe timeout'
        }
    except FileNotFoundError:
        return {
            'duration_seconds': 0,
            'file_size_bytes': 0,
            'success': False,
            'cached': False,
            'error': 'ffprobe not found - install ffmpeg'
        }
    except Exception as e:
        return {
            'duration_seconds': 0,
            'file_size_bytes': 0,
            'success': False,
            'cached': False,
            'error': str(e)
        }


def format_duration(seconds):
    """Format duration in seconds to hours:minutes:seconds."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def format_file_size(bytes_size):
    """Format file size in bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"


def estimate_tokens(text):
    """Estimate token count using a simple heuristic method.
    
    This uses a rough approximation:
    - 1 token ≈ 4 characters for English text
    - Adjusts for whitespace and punctuation
    """
    if not text:
        return 0
    
    # Remove extra whitespace and normalize
    text = ' '.join(text.split())
    
    # Basic token estimation: ~4 chars per token for English
    # This is a rough approximation similar to what OpenAI uses
    char_count = len(text)
    estimated_tokens = char_count / 4
    
    # Adjust for word boundaries (more accurate)
    words = text.split()
    word_count = len(words)
    
    # Use word count as lower bound, char/4 as upper bound
    # Most tokenizers split some words into multiple tokens
    token_estimate = max(word_count, int(estimated_tokens * 0.8))
    
    return token_estimate


def analyze_transcription_file(file_path):
    """Analyze a transcription file for character count, file size, and token estimate."""
    try:
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Read and analyze content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract only the actual transcription text (skip headers and comments)
        transcription_lines = []
        for line in content.split('\n'):
            line = line.strip()
            # Skip empty lines, headers (starting with #), and section markers
            if line and not line.startswith('#') and not line.startswith('='):
                # Remove timestamp prefixes like "[02:15 - 02:45] SPEAKER_A: "
                if ']' in line and line.startswith('['):
                    # Find the end of the timestamp and speaker
                    speaker_end = line.find(': ')
                    if speaker_end != -1:
                        actual_text = line[speaker_end + 2:]
                        transcription_lines.append(actual_text)
                else:
                    transcription_lines.append(line)
        
        # Join all actual transcription text
        transcription_text = ' '.join(transcription_lines)
        
        return {
            'file_size_bytes': file_size,
            'total_characters': len(content),
            'transcription_characters': len(transcription_text),
            'estimated_tokens': estimate_tokens(transcription_text),
            'success': True
        }
        
    except Exception as e:
        return {
            'file_size_bytes': 0,
            'total_characters': 0,
            'transcription_characters': 0,
            'estimated_tokens': 0,
            'success': False,
            'error': str(e)
        }


def main():
    """Main function to analyze audio file statistics."""
    print("📊 Starting audio file statistics analysis...")
    
    # Load episode data
    print("📂 Loading episode data...")
    data = load_episodes_data()
    episodes = data.get('episodes', [])
    
    if not episodes:
        print("No episodes found in episodes.json")
        return
    
    # Filter episodes that have audio files
    episodes_with_files = [ep for ep in episodes if 'file_path' in ep and ep['file_path'] and os.path.exists(ep['file_path'])]
    episodes_without_files = [ep for ep in episodes if 'file_path' not in ep or not ep['file_path'] or not os.path.exists(ep.get('file_path', ''))]
    
    # Filter episodes that have dates
    episodes_with_dates = [ep for ep in episodes if 'date' in ep and ep['date'] is not None and ep['date'] != '']
    episodes_without_dates = [ep for ep in episodes if 'date' not in ep or ep['date'] is None or ep['date'] == '']
    date_percentage = (len(episodes_with_dates) / len(episodes)) * 100 if episodes else 0
    
    # Filter episodes that have transcriptions (check both local and AssemblyAI)
    episodes_with_transcriptions_local = [ep for ep in episodes if 'transcription_file_path' in ep and ep['transcription_file_path'] and os.path.exists(ep['transcription_file_path'])]
    episodes_with_transcriptions_assemblyai = [ep for ep in episodes if 'transcription_file_path_assemblyai' in ep and ep['transcription_file_path_assemblyai'] and os.path.exists(ep['transcription_file_path_assemblyai'])]
    
    # Total unique episodes with any transcription
    episodes_with_any_transcription = set()
    episodes_with_any_transcription.update(ep['url'] for ep in episodes_with_transcriptions_local)
    episodes_with_any_transcription.update(ep['url'] for ep in episodes_with_transcriptions_assemblyai)
    episodes_with_transcriptions_count = len(episodes_with_any_transcription)
    
    # Filter episodes with failed transcriptions (have transcription path but file doesn't exist)
    episodes_with_failed_transcriptions = []
    for ep in episodes_with_files:
        has_local_path = 'transcription_file_path' in ep and ep['transcription_file_path']
        has_assemblyai_path = 'transcription_file_path_assemblyai' in ep and ep['transcription_file_path_assemblyai']
        
        local_exists = has_local_path and os.path.exists(ep['transcription_file_path'])
        assemblyai_exists = has_assemblyai_path and os.path.exists(ep['transcription_file_path_assemblyai'])
        
        # Failed if has a transcription path but file doesn't exist
        if (has_local_path and not local_exists) or (has_assemblyai_path and not assemblyai_exists):
            episodes_with_failed_transcriptions.append(ep)
    
    print(f"\n📋 Found {len(episodes)} total episodes")
    print(f"   📅 {len(episodes_with_dates)} episodes have dates ({date_percentage:.1f}%)")
    print(f"   📁 {len(episodes_with_files)} episodes have audio files")
    print(f"   📝 {episodes_with_transcriptions_count} episodes have transcriptions")
    print(f"     🤖 {len(episodes_with_transcriptions_local)} with local transcriptions")
    print(f"     🌐 {len(episodes_with_transcriptions_assemblyai)} with AssemblyAI transcriptions")
    if episodes_without_dates:
        print(f"   ⚠️  {len(episodes_without_dates)} episodes missing dates")
    if episodes_without_files:
        print(f"   ⚠️  {len(episodes_without_files)} episodes missing audio files")
    if episodes_with_failed_transcriptions:
        example_file = episodes_with_failed_transcriptions[0].get('file_path', 'Unknown')
        if len(episodes_with_failed_transcriptions) == 1:
            print(f"   ❌ 1 episode has failed transcription: {example_file}")
        else:
            print(f"   ❌ {len(episodes_with_failed_transcriptions)} episodes have failed transcriptions (e.g., {example_file})")
    
    if not episodes_with_files:
        print("No episodes with audio files found. Run 'make download' first.")
        return
    
    # Initialize statistics
    stats = {
        'analysis_date': datetime.now().isoformat(),
        'total_episodes': len(episodes),
        'episodes_with_dates': len(episodes_with_dates),
        'episodes_with_files': len(episodes_with_files),
        'episodes_with_transcriptions': episodes_with_transcriptions_count,
        'episodes_with_failed_transcriptions': len(episodes_with_failed_transcriptions),
        'file_details': [],
        'failed_transcriptions': [],
        'summary': {}
    }
    
    # Analyze each audio file
    print(f"\n🔍 Analyzing {len(episodes_with_files)} audio files...")
    
    total_duration = 0
    total_size = 0
    successful_analyses = 0
    failed_analyses = 0
    cached_count = 0
    new_analyses = 0
    episodes_data_updated = False
    
    with tqdm(
        total=len(episodes_with_files),
        desc="📊 Audio Analysis",
        unit="files",
        ncols=100
    ) as pbar:
        
        for episode in episodes_with_files:
            file_path = episode['file_path']
            title = episode.get('title', 'Unknown')
            
            # Get audio file information (with caching)
            audio_info = get_audio_info(file_path, episode)
            
            # Update episode metadata if new analysis was performed
            if audio_info['success'] and not audio_info.get('cached', False):
                episode['audio_metadata'] = {
                    'file_size_bytes': audio_info['file_size_bytes'],
                    'duration_seconds': audio_info['duration_seconds'],
                    'analyzed_date': datetime.now().isoformat()
                }
                # Save immediately after each new analysis
                save_episodes_data(data)
                episodes_data_updated = True
                new_analyses += 1
            elif audio_info.get('cached', False):
                cached_count += 1
            
            # Create file detail record
            file_detail = {
                'title': title,
                'url': episode['url'],
                'file_path': file_path,
                'file_size_bytes': audio_info['file_size_bytes'],
                'duration_seconds': audio_info['duration_seconds'],
                'success': audio_info['success'],
                'cached': audio_info.get('cached', False)
            }
            
            if not audio_info['success']:
                file_detail['error'] = audio_info['error']
                failed_analyses += 1
            else:
                successful_analyses += 1
                total_duration += audio_info['duration_seconds']
                total_size += audio_info['file_size_bytes']
            
            stats['file_details'].append(file_detail)
            pbar.update(1)
    
    # Final status message
    if new_analyses > 0:
        print(f"\n✅ Saved metadata for {new_analyses} episodes during analysis")
    
    if cached_count > 0:
        print(f"⚡ Used cached data for {cached_count} episodes (faster analysis)")
    
    # Collect failed transcription details
    for ep in episodes_with_failed_transcriptions:
        failed_detail = {
            'title': ep.get('title', 'Unknown'),
            'url': ep['url'],
            'file_path': ep.get('file_path', 'Unknown'),
            'transcription_file_path': ep.get('transcription_file_path'),
            'transcription_file_path_assemblyai': ep.get('transcription_file_path_assemblyai'),
            'local_exists': ep.get('transcription_file_path') and os.path.exists(ep['transcription_file_path']),
            'assemblyai_exists': ep.get('transcription_file_path_assemblyai') and os.path.exists(ep['transcription_file_path_assemblyai'])
        }
        stats['failed_transcriptions'].append(failed_detail)
    
    # Analyze transcription files
    print(f"\n🔍 Analyzing transcription files...")
    
    transcription_stats = {
        'total_files': 0,
        'total_file_size_bytes': 0,
        'total_characters': 0,
        'total_transcription_characters': 0,
        'total_estimated_tokens': 0,
        'local_files': 0,
        'assemblyai_files': 0,
        'failed_analyses': 0
    }
    
    # Analyze all transcription files
    all_transcription_files = []
    
    # Check local transcriptions
    for episode in episodes_with_transcriptions_local:
        if 'transcription_file_path' in episode and episode['transcription_file_path']:
            all_transcription_files.append({
                'path': episode['transcription_file_path'],
                'type': 'local',
                'title': episode.get('title', 'Unknown')
            })
    
    # Check AssemblyAI transcriptions
    for episode in episodes_with_transcriptions_assemblyai:
        if 'transcription_file_path_assemblyai' in episode and episode['transcription_file_path_assemblyai']:
            all_transcription_files.append({
                'path': episode['transcription_file_path_assemblyai'],
                'type': 'assemblyai',
                'title': episode.get('title', 'Unknown')
            })
    
    if all_transcription_files:
        with tqdm(
            total=len(all_transcription_files),
            desc="📝 Transcription Analysis",
            unit="files",
            ncols=100
        ) as trans_pbar:
            
            for trans_file in all_transcription_files:
                if os.path.exists(trans_file['path']):
                    analysis = analyze_transcription_file(trans_file['path'])
                    
                    if analysis['success']:
                        transcription_stats['total_files'] += 1
                        transcription_stats['total_file_size_bytes'] += analysis['file_size_bytes']
                        transcription_stats['total_characters'] += analysis['total_characters']
                        transcription_stats['total_transcription_characters'] += analysis['transcription_characters']
                        transcription_stats['total_estimated_tokens'] += analysis['estimated_tokens']
                        
                        if trans_file['type'] == 'local':
                            transcription_stats['local_files'] += 1
                        else:
                            transcription_stats['assemblyai_files'] += 1
                    else:
                        transcription_stats['failed_analyses'] += 1
                
                trans_pbar.update(1)
        
        print(f"✅ Analyzed {transcription_stats['total_files']} transcription files")
        if transcription_stats['failed_analyses'] > 0:
            print(f"⚠️  {transcription_stats['failed_analyses']} transcription files failed analysis")
    else:
        print("📝 No transcription files found")
    
    # Calculate summary statistics
    transcription_percentage = (episodes_with_transcriptions_count / len(episodes)) * 100 if episodes else 0
    average_duration = total_duration / successful_analyses if successful_analyses > 0 else 0
    
    # Convert totals to human-readable formats
    total_size_gb = total_size / (1024**3)  # Convert to GB
    total_duration_hours = total_duration / 3600  # Convert to hours
    
    # Calculate AssemblyAI cost estimation at $0.12 per hour
    assemblyai_cost_per_hour = 0.12
    estimated_total_cost = total_duration_hours * assemblyai_cost_per_hour
    estimated_remaining_cost = 0
    
    # Calculate cost for untranscribed episodes
    untranscribed_episodes = [ep for ep in episodes_with_files if ep['url'] not in episodes_with_any_transcription]
    if untranscribed_episodes:
        untranscribed_duration = 0
        for episode in untranscribed_episodes:
            for file_detail in stats['file_details']:
                if file_detail['url'] == episode['url'] and file_detail['success']:
                    untranscribed_duration += file_detail['duration_seconds']
                    break
        estimated_remaining_cost = (untranscribed_duration / 3600) * assemblyai_cost_per_hour
    
    stats['summary'] = {
        'total_mp3_files': successful_analyses,
        'failed_analyses': failed_analyses,
        'cached_analyses': cached_count,
        'new_analyses': new_analyses,
        'date_statistics': {
            'episodes_with_dates': len(episodes_with_dates),
            'episodes_without_dates': len(episodes_without_dates),
            'date_percentage': round(date_percentage, 1)
        },
        'total_size_bytes': total_size,
        'total_size_gb': round(total_size_gb, 2),
        'total_size_formatted': format_file_size(total_size),
        'total_duration_seconds': total_duration,
        'total_duration_hours': round(total_duration_hours, 2),
        'total_duration_formatted': format_duration(total_duration),
        'average_duration_seconds': average_duration,
        'average_duration_formatted': format_duration(average_duration),
        'transcription_percentage': round(transcription_percentage, 1),
        'transcription_counts': {
            'total_with_transcriptions': episodes_with_transcriptions_count,
            'local_transcriptions': len(episodes_with_transcriptions_local),
            'assemblyai_transcriptions': len(episodes_with_transcriptions_assemblyai)
        },
        'cost_estimation': {
            'assemblyai_rate_per_hour': assemblyai_cost_per_hour,
            'estimated_total_cost': round(estimated_total_cost, 2),
            'estimated_remaining_cost': round(estimated_remaining_cost, 2),
            'total_hours_for_costing': round(total_duration_hours, 2)
        },
        'transcription_analysis': {
            'total_transcription_files': transcription_stats['total_files'],
            'local_transcription_files': transcription_stats['local_files'],
            'assemblyai_transcription_files': transcription_stats['assemblyai_files'],
            'total_file_size_bytes': transcription_stats['total_file_size_bytes'],
            'total_file_size_formatted': format_file_size(transcription_stats['total_file_size_bytes']),
            'total_characters': transcription_stats['total_characters'],
            'total_transcription_characters': transcription_stats['total_transcription_characters'],
            'estimated_total_tokens': transcription_stats['total_estimated_tokens'],
            'failed_transcription_analyses': transcription_stats['failed_analyses']
        }
    }
    
    # Save statistics to JSON file
    print(f"\n💾 Saving statistics to stats.json...")
    try:
        with open('stats.json', 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        print(f"✅ Statistics saved to stats.json")
    except IOError as e:
        print(f"❌ Error saving stats.json: {e}")
    
    # Display summary
    print(f"\n📊 VOXOLOGY PODCAST STATISTICS")
    print(f"=" * 60)
    print(f"📁 Total MP3 files analyzed:     {successful_analyses:,}")
    if cached_count > 0:
        print(f"⚡ Used cached metadata:         {cached_count:,}")
    if new_analyses > 0:
        print(f"🔍 New analyses performed:       {new_analyses:,}")
    if failed_analyses > 0:
        print(f"❌ Failed analyses:              {failed_analyses:,}")
        
        # Show details of failed analyses
        print(f"\n❌ FAILED ANALYSIS DETAILS:")
        print(f"=" * 60)
        failed_files = [detail for detail in stats['file_details'] if not detail['success']]
        for i, failed_file in enumerate(failed_files, 1):
            print(f"{i}. {failed_file['title']}")
            print(f"   📁 File: {failed_file['file_path']}")
            print(f"   🚫 Error: {failed_file.get('error', 'Unknown error')}")
            print()
    print(f"💾 Total size:                   {stats['summary']['total_size_formatted']} ({total_size_gb:.2f} GB)")
    print(f"⏱️  Total duration:               {stats['summary']['total_duration_formatted']} ({total_duration_hours:.1f} hours)")
    print(f"📊 Average episode duration:     {stats['summary']['average_duration_formatted']}")
    print(f"📝 Episodes with transcriptions: {transcription_percentage:.1f}% ({episodes_with_transcriptions_count}/{len(episodes)})")
    print(f"   🤖 Local transcriptions:      {len(episodes_with_transcriptions_local)}")
    print(f"   🌐 AssemblyAI transcriptions: {len(episodes_with_transcriptions_assemblyai)}")
    
    # Transcription text analysis section
    if transcription_stats['total_files'] > 0:
        print(f"\n📝 TRANSCRIPTION TEXT ANALYSIS")
        print(f"=" * 60)
        print(f"📄 Total transcription files:    {transcription_stats['total_files']:,}")
        print(f"   🤖 Local files:               {transcription_stats['local_files']:,}")
        print(f"   🌐 AssemblyAI files:          {transcription_stats['assemblyai_files']:,}")
        print(f"💾 Total transcription size:     {format_file_size(transcription_stats['total_file_size_bytes'])}")
        print(f"🔤 Total characters (all):       {transcription_stats['total_characters']:,}")
        print(f"💬 Transcription text chars:     {transcription_stats['total_transcription_characters']:,}")
        print(f"🎯 Estimated tokens (LLM):       {transcription_stats['total_estimated_tokens']:,}")
        
        # Calculate some useful ratios
        if transcription_stats['total_characters'] > 0:
            text_ratio = (transcription_stats['total_transcription_characters'] / transcription_stats['total_characters']) * 100
            print(f"📊 Text vs metadata ratio:       {text_ratio:.1f}% actual transcription")
        
        if transcription_stats['total_transcription_characters'] > 0:
            chars_per_token = transcription_stats['total_transcription_characters'] / transcription_stats['total_estimated_tokens']
            print(f"🔢 Average chars per token:      {chars_per_token:.1f}")
    
    # Series analysis section
    series_data = load_series_data()
    if series_data:
        print(f"\n📚 SERIES ANALYSIS")
        print(f"=" * 60)
        
        # Count total episodes in series analysis
        total_episodes_in_series = 0
        series_list = []
        
        for series_name, episodes_in_series in series_data.items():
            if series_name == "INDEPENDENT":
                # INDEPENDENT episodes are stored as a list
                episode_count = len(episodes_in_series) if isinstance(episodes_in_series, list) else len(episodes_in_series.values())
            else:
                # Regular series are stored as dictionaries
                episode_count = len(episodes_in_series)
                series_list.append((series_name, episode_count))
            
            total_episodes_in_series += episode_count
        
        # Calculate statistics
        series_percentage = (total_episodes_in_series / len(episodes_with_files)) * 100 if episodes_with_files else 0
        num_series = len(series_list)  # Exclude INDEPENDENT from series count
        
        # Calculate average episodes per series (excluding INDEPENDENT)
        avg_episodes_per_series = sum(count for _, count in series_list) / num_series if num_series > 0 else 0
        
        # Display summary stats
        print(f"📊 Episodes parsed into series:   {series_percentage:.1f}% ({total_episodes_in_series}/{len(episodes_with_files)})")
        print(f"📖 Number of series identified:   {num_series}")
        if num_series > 0:
            print(f"📈 Average episodes per series:   {avg_episodes_per_series:.1f}")
        
        # Display INDEPENDENT count
        independent_count = 0
        if "INDEPENDENT" in series_data:
            independent_episodes = series_data["INDEPENDENT"]
            independent_count = len(independent_episodes) if isinstance(independent_episodes, list) else len(independent_episodes.values())
            print(f"🎯 Independent episodes:          {independent_count}")
        
        # List all series with episode counts
        if series_list:
            print(f"\n📚 SERIES BREAKDOWN:")
            # Sort by episode count (descending)
            series_list.sort(key=lambda x: x[1], reverse=True)
            for series_name, episode_count in series_list:
                print(f"  📖 {series_name}: {episode_count} episodes")
    else:
        print(f"\n📚 SERIES ANALYSIS")
        print(f"=" * 60)
        print(f"📖 No series data found. Run 'make series' to analyze episodes.")
    
    # Cost estimation section
    print(f"\n💰 ASSEMBLYAI COST ESTIMATION (${assemblyai_cost_per_hour:.2f}/hour)")
    print(f"=" * 60)
    print(f"💵 Total cost for all audio:     ${estimated_total_cost:.2f}")
    if estimated_remaining_cost > 0:
        print(f"⏳ Cost for remaining episodes:  ${estimated_remaining_cost:.2f}")
        print(f"   ({len(untranscribed_episodes)} episodes not yet transcribed)")
    else:
        print(f"✅ All episodes transcribed!")
    
    if episodes_without_files:
        print(f"\n⚠️  Note: {len(episodes_without_files)} episodes don't have audio files yet")
        print(f"   Run 'make download' to download missing files")
    
    # Failed transcriptions section
    if episodes_with_failed_transcriptions:
        print(f"\n❌ FAILED TRANSCRIPTION DETAILS")
        print(f"=" * 60)
        for i, failed_ep in enumerate(episodes_with_failed_transcriptions, 1):
            print(f"{i}. {failed_ep.get('title', 'Unknown')}")
            print(f"   📁 Audio: {failed_ep.get('file_path', 'Unknown')}")
            
            # Show which transcription paths exist/don't exist
            if failed_ep.get('transcription_file_path'):
                status = "✅ exists" if os.path.exists(failed_ep['transcription_file_path']) else "❌ missing"
                print(f"   🤖 Local: {failed_ep['transcription_file_path']} ({status})")
            
            if failed_ep.get('transcription_file_path_assemblyai'):
                status = "✅ exists" if os.path.exists(failed_ep['transcription_file_path_assemblyai']) else "❌ missing"
                print(f"   🌐 AssemblyAI: {failed_ep['transcription_file_path_assemblyai']} ({status})")
            print()
    
    print(f"\n📋 Detailed statistics saved to: ./stats.json")


if __name__ == "__main__":
    main()