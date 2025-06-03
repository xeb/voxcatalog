#!/usr/bin/env python3
"""
lunches.py - Script to extract lunch menu information from CVCS website
and save it to a JSON file.

Required packages:
    pip install -q -U google-genai requests
"""

import json
import os
import re
import datetime
from datetime import datetime
import requests
from google import genai

def get_api_key():
    """Reads the API key from ~/.ssh/gemini_api_key.txt."""
    print("Getting API key...")
    home_dir = os.path.expanduser("~")
    api_key_path = os.path.join(home_dir, ".ssh", "gemini_api_key.txt")

    try:
        with open(api_key_path, "r") as f:
            api_key = f.read().strip()
        print("API key retrieved successfully")
        return api_key
    except FileNotFoundError:
        print(f"Error: API key file not found at {api_key_path}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def extract_lunch_data(html_content):
    """
    Use Gemini API to extract lunch menu information from the HTML content.
    """
    print("Extracting lunch data from HTML...")
    api_key = get_api_key()

    if not api_key:
        print("API key not loaded. Exiting.")
        return []

    print("Initializing Gemini client...")
    client = genai.Client(api_key=api_key, http_options={'api_version': 'v1alpha'})

    print("Creating prompt and schema for Gemini...")

    # Define the JSON schema for structured output
    json_schema = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "day": {
                    "type": "string",
                    "description": "The day of the week (Monday, Tuesday, etc.)"
                },
                "date": {
                    "type": "string",
                    "description": "The date in ISO format (YYYY-MM-DD)"
                },
                "menu_item": {
                    "type": "string",
                    "description": "The lunch menu item"
                }
            },
            "required": ["day", "date", "menu_item"]
        }
    }

    # Create a prompt for Gemini to extract the lunch information
    prompt = """
    Extract all lunch menu information from the following HTML content.
    For each day, provide:
    1. The day of the week (Monday, Tuesday, etc.)
    2. The date in ISO format (YYYY-MM-DD)
    3. The lunch menu item(s)

    Only include days that have lunch items (not just breakfast).
    """

    try:
        # Generate the response using the 2.5-pro model with structured output
        print("Sending request to Gemini API with structured output...")
        response = client.models.generate_content(
            model='gemini-2.5-pro-preview-05-06',
            contents=prompt + "\n\nHTML content:\n" + html_content,
            config={
                'response_mime_type': 'application/json',
                'response_schema': json_schema
            }
        )
        print("Response received from Gemini API")

        # Parse the JSON from the response
        print("Parsing JSON from structured response...")
        try:
            # Get the JSON response from text
            structured_data = response.text
            return json.loads(structured_data)
        except Exception as e:
            print(f"Error parsing structured response: {e}")
            print(f"Response: {response}")
            return []
    except Exception as e:
        print(f"An error occurred during API call: {e}")
        return []

def fetch_menu_page():
    """Fetch the menu page content from the CVCS website."""
    print("Fetching menu page from CVCS website...")
    url = "https://www.cvcs.org/hub/daily-menu"
    response = requests.get(url)
    if response.status_code == 200:
        print("Menu page fetched successfully")
        return response.text
    else:
        print(f"Failed to fetch the menu page. Status code: {response.status_code}")
        return None

def save_to_json(data, filename="lunches.json"):
    """Save the extracted data to a JSON file."""
    print(f"Saving data to {filename}...")
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Data saved to {filename}")

def main():
    """Main function to run the script."""
    print("Starting lunch menu extraction process...")
    # Fetch the menu page
    html_content = fetch_menu_page()
    if not html_content:
        print("Exiting due to failure in fetching menu page")
        return

    # Extract lunch data using Gemini
    lunch_data = extract_lunch_data(html_content)
    print(f"Extracted {len(lunch_data)} lunch menu items")

    # Save to JSON file
    save_to_json(lunch_data)
    print("Process completed successfully")

if __name__ == "__main__":
    main()
