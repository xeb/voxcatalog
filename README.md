# Voxology Catalog

A comprehensive AI-powered tool for downloading, transcribing, and organizing the Voxology podcast. The goal is to create a searchable catalog that organizes episodes into series and enhances episode discovery using modern AI technologies.

💝 _This project was lovingly made entirely with [Claude Code](https://claude.ai/code) for <$20 of API credits_ 🤖✨

## 🎯 Purpose

The Voxology Catalog aims to:
- **Download** all episodes from the Voxology podcast website with metadata
- **Transcribe** audio content using AssemblyAI with speaker diarization
- **Organize** episodes by series using Gemini AI analysis
- **Enhance discovery** of related episodes and themes
- **Analyze** content statistics and costs

## 🚀 Quick Start

### Prerequisites
```bash
pip install -r requirements.txt
```

**Required API Keys:**
- AssemblyAI API key in `~/.ssh/assemblyai.txt`
- Gemini API key in `~/.ssh/gemini_api_key.txt`

### One-Command Workflow
```bash
# Run the complete end-to-end workflow
make all
```

### Step-by-Step Workflow
Run these commands in order:

```bash
# 1. Scrape episodes (URLs, titles, dates) and extract audio links
make episodes

# 2. Download audio files
make download

# 3. Transcribe with AI speaker diarization
make transcribe

# 4. Analyze for series patterns
make series

# 5. Generate comprehensive statistics (optional)
make stats

# 6. Export data to CSV format (optional)
make csv
```

## 📋 Available Commands

| Command | Description |
|---------|-------------|
| `make help` | Show all available commands with banner |
| `make all` | **Complete workflow: episodes → download → transcribe → series → stats** |
| `make episodes` | Scrape episode metadata and extract audio download links |
| `make download` | Download audio files to catalog directory |
| `make transcribe` | Transcribe audio using AssemblyAI with speaker labels |
| `make series` | Analyze transcriptions to identify series using Gemini AI |
| `make stats` | Generate statistics (audio, transcriptions, tokens, costs) |
| `make csv` | Export series and episode data to CSV format |

## 📁 Project Structure

```
voxcatalog/
├── get_episode_links.py           # Scrapes episode URLs and metadata
├── get_episode_audio_links.py     # Extracts audio download links
├── get_audio_files.py             # Downloads audio files
├── transcribe-assemblyai.py       # AI transcription with speaker diarization
├── parse_series.py                # AI series analysis using Gemini
├── stats.py                       # Comprehensive statistics and analysis
├── parse_csv.py                   # CSV data export
├── episodes.json                  # Master episode database
├── series.json                    # Series organization data
├── stats.json                     # Detailed statistics
├── voxology_catalog.csv           # Spreadsheet-friendly data export
├── catalog/                       # Downloaded audio files and transcriptions
├── requirements.txt               # Python dependencies
├── Makefile                       # Command shortcuts
└── CLAUDE.md                      # Development guidance
```

## 🗃️ Data Formats

### episodes.json
```json
{
  "episodes": [
    {
      "url": "https://www.voxologypodcast.com/episode-name/",
      "page": 1,
      "title": "Episode Title",
      "date": "2025-06-02",
      "audio_link": "https://media.../episode.mp3",
      "file_path": "catalog/episode-name.mp3",
      "transcription_file_path_assemblyai": "catalog/episode-name-assemblyai.txt",
      "audio_metadata": {
        "file_size_bytes": 15234567,
        "duration_seconds": 1825.4,
        "analyzed_date": "2025-01-02T15:30:45"
      }
    }
  ],
  "processed_pages": [1, 2, 3, ...],
  "last_updated": "2025-01-02T12:34:56"
}
```

### series.json
```json
{
  "INDEPENDENT": [
    "catalog/episode-1.mp3",
    "catalog/episode-5.mp3"
  ],
  "Exile Series": {
    "1": "catalog/exile-part-1.mp3", 
    "2": "catalog/exile-part-2.mp3"
  }
}
```

### voxology_catalog.csv
```csv
series_name,episode_num,episode_date,episode_url,episode_file_path_mp3
INDEPENDENT,1,2025-01-15,https://www.voxologypodcast.com/episode-1/,catalog/episode-1.mp3
Exile Series,1,2025-01-10,https://www.voxologypodcast.com/exile-part-1/,catalog/exile-part-1.mp3
Exile Series,2,2025-01-12,https://www.voxologypodcast.com/exile-part-2/,catalog/exile-part-2.mp3
```

## ✨ Features

### 🔄 Smart Processing
- **Resumable Processing**: All scripts can be safely interrupted and resumed
- **Progress Tracking**: Real-time progress bars with tqdm
- **Duplicate Detection**: Skips already processed episodes and downloads
- **Date Updates**: Automatically updates missing episode dates
- **Caching**: Reuses audio metadata to speed up statistics

### 🤖 AI Integration
- **AssemblyAI Transcription**: Professional-quality speech-to-text with speaker diarization
- **Gemini Series Analysis**: AI-powered identification of podcast series patterns
- **Conservative Classification**: Only groups episodes into series when explicitly clear

### 📊 Comprehensive Analytics
- **Audio Statistics**: Duration, file sizes, storage requirements
- **Transcription Analysis**: Character counts, token estimates for LLM processing
- **Cost Estimation**: AssemblyAI transcription costs at $0.12/hour
- **Series Organization**: Automated categorization of episodes
- **Failed Transcription Detection**: Identifies episodes needing retry
- **CSV Export**: Spreadsheet-friendly data export for external analysis

## 🔄 Resume Capability

Each script tracks its progress and can resume from where it left off:
- **Episodes**: Skips processed pages, updates missing dates automatically
- **Audio Links**: Skips episodes that already have audio_link field
- **Downloads**: Skips files that already exist, updates JSON progressively
- **Transcriptions**: Skips completed transcriptions, updates JSON per episode
- **Series Analysis**: Skips already analyzed episodes, saves progress continuously
- **CSV Export**: Generates fresh export from current data state

## 📊 Current Status

The Voxology podcast collection includes:
- **23 pages** of episodes on the website
- **538 total episodes** across all pages
- **100% episodes have dates** (538/538)
- **Average episode duration**: ~60 minutes
- **Total collection**: ~535 hours of content
- **Storage requirements**: ~43GB for audio files
- **Transcription progress**: 14.5% complete (78/538 episodes)
- **Series identification**: 2 series discovered + independent episodes

## 💰 Cost Estimates

Based on current collection:
- **Total transcription cost**: ~$64.23 (at $0.12/hour)
- **Remaining transcription cost**: ~$53.94 (460 episodes left)
- **Average cost per episode**: ~$0.12

## 🎵 About Voxology

Voxology is a podcast exploring theology, culture, and the intersection of faith and society. The catalog helps organize the extensive archive of episodes for easier navigation and discovery of related content and series.

## 🛠️ Development

See `CLAUDE.md` for development guidance and architectural notes.