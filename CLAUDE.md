# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a web scraping project containing Python scripts for extracting content from websites and saving structured data to JSON files. The primary focus is on:

1. **Podcast episode scraping** (`get_episode_links.py`) - Scrapes episode links from the Voxology podcast website
2. **Lunch menu extraction** (`lunches.py`) - Extracts lunch menu data from CVCS website using Gemini AI

## Common Commands

### Setup
```bash
pip install -r requirements.txt
```

### Running Scripts
```bash
# Scrape podcast episodes (resumes from last processed page)
python get_episode_links.py

# Extract lunch menus (requires Gemini API key at ~/.ssh/gemini_api_key.txt)
python lunches.py
```

## Code Architecture

### Episode Scraper (`get_episode_links.py`)
- **Resumable scraping**: Uses `episodes.json` to track processed pages and avoid re-processing
- **Data structure**: JSON format with episode URL, page number, title, and processing metadata
- **Error handling**: Implements retry logic with sleep delays for failed requests
- **CSS selector targeting**: Uses specific selectors (`.card-body a.mt-4[href]`) to extract episode links
- **Rate limiting**: Built-in delays between requests to be respectful to the target website

### Lunch Menu Extractor (`lunches.py`)
- **AI-powered extraction**: Uses Google Gemini API with structured output schemas
- **External API integration**: Requires API key stored in `~/.ssh/gemini_api_key.txt`
- **Structured output**: Defines JSON schemas to ensure consistent data extraction
- **Date parsing**: Extracts and formats dates from menu content

### Data Storage
- **episodes.json**: Contains scraped podcast episodes with metadata (URL, page, title, timestamps)
- **episodes.txt**: Simple text file with just URLs for compatibility
- **lunches.json**: Structured lunch menu data with days, dates, and menu items

## Dependencies
- `requests`: HTTP requests for web scraping
- `beautifulsoup4`: HTML parsing and CSS selector support
- `google-genai`: Google Gemini AI API integration (for lunch menu script)