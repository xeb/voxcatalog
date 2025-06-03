# Voxology Catalog

A comprehensive tool for downloading, transcribing, and organizing the Voxology podcast. The goal is to create a searchable catalog that organizes episodes into series and enhances episode discovery.

## 🎯 Purpose

The Voxology Catalog aims to:
- **Download** all episodes from the Voxology podcast website
- **Transcribe** audio content for searchability
- **Organize** episodes by series and topics
- **Enhance discovery** of related episodes and themes

## 🚀 Quick Start

### Prerequisites
```bash
pip install -r requirements.txt
```

### Basic Workflow
Run these commands in order:

```bash
# 1. Scrape episode links from website
make episodelinks

# 2. Extract audio download links
make audiolinks  

# 3. Download audio files
make download
```

## 📋 Available Commands

| Command | Description |
|---------|-------------|
| `make help` | Show all available commands with banner |
| `make episodelinks` | Scrape episode links from Voxology podcast website |
| `make audiolinks` | Extract MP3/M4A audio links from episode pages |
| `make download` | Download audio files to catalog directory |

## 📁 Project Structure

```
voxcatalog/
├── get_episode_links.py      # Scrapes episode URLs from website
├── get_episode_audio_links.py # Extracts audio download links
├── get_audio_files.py        # Downloads audio files
├── episodes.json             # Master episode database
├── catalog/                  # Downloaded audio files
├── requirements.txt          # Python dependencies
├── Makefile                  # Command shortcuts
└── CLAUDE.md                 # Development guidance
```

## 🗃️ Data Format

The `episodes.json` file contains:
```json
{
  "episodes": [
    {
      "url": "https://www.voxologypodcast.com/episode-name/",
      "page": 1,
      "title": "Episode Title",
      "audio_link": "https://media.../episode.mp3",
      "file_path": "catalog/episode-name.mp3"
    }
  ],
  "processed_pages": [1, 2, 3, ...],
  "last_updated": "2025-01-02T12:34:56"
}
```

## ✨ Features

- **Resumable Processing**: All scripts can be safely interrupted and resumed
- **Progress Tracking**: Real-time progress bars with tqdm
- **Duplicate Detection**: Skips already processed episodes and downloads
- **Error Handling**: Robust retry logic and failure recovery
- **Clean Output**: Minimal logging focused on progress visibility

## 🔄 Resume Capability

Each script tracks its progress and can resume from where it left off:
- **Episode Links**: Skips already processed pages
- **Audio Links**: Skips episodes that already have audio_link field
- **Downloads**: Skips files that already exist in catalog/

## 📊 Current Status

The Voxology podcast has approximately:
- **23 pages** of episodes on the website
- **538 total episodes** across all pages
- Episodes include both **MP3** and **M4A** audio formats

## 🎵 About Voxology

Voxology is a podcast exploring theology, culture, and the intersection of faith and society. The catalog helps organize the extensive archive of episodes for easier navigation and discovery of related content and series.

## 🛠️ Development

See `CLAUDE.md` for development guidance and architectural notes.