# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a comprehensive AI-powered podcast catalog system for the Voxology podcast. The project implements a complete pipeline from web scraping to AI-powered analysis:

1. **Episode Discovery** - Scrapes episode metadata from podcast website with smart resumable processing
2. **Audio Download** - Downloads all podcast audio files with progress tracking
3. **AI Transcription** - Uses AssemblyAI for professional transcription with speaker diarization
4. **Series Analysis** - Leverages Gemini AI to identify podcast series patterns and relationships
5. **Statistical Analysis** - Provides comprehensive analytics on content, costs, and progress

## Common Commands

### Setup
```bash
pip install -r requirements.txt
```

### Complete Workflow
```bash
# Run entire pipeline from scraping to analysis
make all

# Individual steps (run in order)
make episodes   # Scrape episodes and extract audio links
make download   # Download audio files
make transcribe # AI transcription with AssemblyAI
make series     # AI series analysis with Gemini
make stats      # Generate comprehensive statistics
make csv        # Export data to CSV format
```

### Development and Debugging
```bash
# Show all available commands
make help

# Run individual scripts directly for debugging
python get_episode_links.py      # Episode scraping only
python get_episode_audio_links.py # Audio link extraction only  
python get_audio_files.py        # Download audio files
python transcribe-assemblyai.py  # Transcription only
python parse_series.py           # Series analysis only
python stats.py                  # Statistics only
python parse_csv.py              # CSV export only
```

## Code Architecture

### Pipeline Flow
The project follows a strict sequential pipeline where each stage depends on the previous:
1. `episodes.json` ← Episode scraping and audio link extraction
2. `catalog/*.mp3` ← Audio file downloads
3. `catalog/*-assemblyai.txt` ← AI transcriptions
4. `series.json` ← AI series analysis
5. `stats.json` ← Comprehensive analytics
6. `voxology_catalog.csv` ← CSV export for external analysis

### Key Components

#### Episode Discovery (`get_episode_links.py`, `get_episode_audio_links.py`)
- **Smart resumability**: Tracks processed pages and missing data to avoid re-work
- **Date parsing**: Handles multiple date formats including "Sept. 18, 2024"
- **Selective processing**: Only re-processes pages with episodes missing dates
- **Audio link extraction**: Finds direct download URLs from episode pages

#### AI Transcription (`transcribe-assemblyai.py`)
- **AssemblyAI integration**: Professional speech-to-text with speaker diarization
- **Progressive saving**: Updates `episodes.json` after each successful transcription
- **Resume capability**: Skips already transcribed episodes
- **Structured output**: Saves speaker-labeled transcripts to `catalog/` directory

#### AI Series Analysis (`parse_series.py`)
- **Gemini AI integration**: Uses structured output schemas for consistent analysis
- **Conservative classification**: Only groups episodes into series when explicitly clear
- **INDEPENDENT episodes**: Stored as simple arrays, not numbered sequences
- **Resume capability**: Skips episodes already analyzed (checks `series.json`)
- **Migration logic**: Automatically converts old dict format to new list format

#### Statistics and Analytics (`stats.py`)
- **Smart caching**: Reuses audio metadata to avoid re-analyzing unchanged files
- **Comprehensive metrics**: Audio duration, file sizes, transcription analysis, cost estimation
- **Token estimation**: Calculates LLM token counts for transcription text
- **Date tracking**: Reports episodes with/without dates and completion percentages
- **Failed transcription detection**: Identifies episodes with missing transcription files
- **Series analysis reporting**: Shows series parse percentages and episode distribution

#### Data Export (`parse_csv.py`)
- **CSV generation**: Exports combined series and episode data to spreadsheet format
- **Cross-reference capability**: Matches series data with episode metadata (URLs, dates)
- **Format handling**: Supports both INDEPENDENT list format and numbered series dictionaries
- **Data validation**: Reports missing dates, URLs, and data inconsistencies

### Data Structures

#### episodes.json
Central database tracking all episode metadata, audio files, transcriptions, and processing state.

#### series.json
AI-generated series organization:
- INDEPENDENT episodes: `["file1.mp3", "file2.mp3"]` (simple array)
- Series episodes: `{"1": "file1.mp3", "2": "file2.mp3"}` (numbered dict)

#### stats.json
Complete analytics including audio statistics, transcription analysis, cost estimates, and progress tracking.

#### voxology_catalog.csv
Spreadsheet-friendly export with columns: series_name, episode_num, episode_date, episode_url, episode_file_path_mp3.

### API Integrations

#### AssemblyAI (transcription)
- API key location: `~/.ssh/assemblyai.txt`
- Configuration: Speaker labels, auto highlights, punctuation, text formatting
- Cost: $0.12/hour of audio

#### Google Gemini AI (series analysis)
- API key location: `~/.ssh/gemini_api_key.txt`
- Model: `gemini-2.5-pro-preview-05-06`
- Uses structured output schemas for consistent JSON responses

### Error Handling and Resilience

- **Resume capability**: All scripts can be interrupted and resumed safely
- **Progressive saving**: State saved after each successful operation
- **Smart skipping**: Avoids re-processing already completed work
- **Rate limiting**: Respectful delays between web requests
- **Comprehensive error reporting**: Detailed ffmpeg/API error analysis

## Important Implementation Details

### Date Parsing Quirks
The `parse_episode_date()` function handles inconsistent date formats including "Sept." abbreviation which requires special string replacement.

### INDEPENDENT Episode Storage
INDEPENDENT episodes are stored as simple arrays, not numbered dictionaries, to reflect their non-sequential nature.

### Caching Strategy
Audio metadata is cached in `episodes.json` and reused based on file size matching to avoid expensive ffprobe operations.

### Series Analysis Logic
Gemini AI receives current episode, previous episode context, and existing series data to make informed series classification decisions.

### Statistical Reporting
The stats module provides comprehensive reporting including failed transcription detection, series analysis percentages, and detailed breakdowns of all data types.

## Dependencies
- `requests` + `beautifulsoup4`: Web scraping
- `assemblyai`: Professional AI transcription
- `google-genai`: AI series analysis
- `tqdm`: Progress tracking
- `ffmpeg`/`ffprobe`: Audio metadata extraction