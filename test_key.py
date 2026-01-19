import requests
import json
import os
from pathlib import Path

def test_key_raw():
    # Read the key manually like the app does
    key = None
    try:
        env_path = Path(".env")
        if env_path.exists():
            lines = env_path.read_text().splitlines()
            for line in lines:
                if line.strip().startswith("GOOGLE_API_KEY="):
                    parts = line.split("=", 1)
                    if len(parts) == 2:
                        key = parts[1].strip()
                        if (key.startswith('"') and key.endswith('"')) or \
                           (key.startswith("'") and key.endswith("'")):
                            key = key[1:-1]
                        break
    except Exception as e:
        print(f"Error reading .env: {e}")
        return

    if not key:
        print("Could not find key in .env")
        return

    print(f"Testing Key: {key[:5]}...{key[-5:]}")
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}"
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{
            "parts": [{
                "text": "Hello, this is a test."
            }]
        }]
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")

if __name__ == "__main__":
    test_key_raw()
