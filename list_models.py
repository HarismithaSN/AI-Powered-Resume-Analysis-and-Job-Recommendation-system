import requests
import os
from pathlib import Path

def list_models():
    # Read key
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
                        break
    except Exception: pass
    
    if not key:
        print("No key found")
        return

    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
    response = requests.get(url)
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        models = response.json().get('models', [])
        print("Available Models:")
        for m in models:
            if 'generateContent' in m.get('supportedGenerationMethods', []):
                print(f"- {m['name']}")
    else:
        print(response.text)

if __name__ == "__main__":
    list_models()
