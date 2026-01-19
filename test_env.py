import os
from pathlib import Path
from dotenv import load_dotenv

def test_loading():
    print("--- Diagnostic Start ---")
    current_dir = Path.cwd()
    print(f"Current Working Directory: {current_dir}")
    
    env_path = current_dir / ".env"
    print(f"Expected .env path: {env_path}")
    print(f".env exists?: {env_path.exists()}")
    
    if env_path.exists():
        print(f".env content preview: {env_path.read_text()[:20]}...")
    
    res = load_dotenv(dotenv_path=env_path)
    print(f"load_dotenv result: {res}")
    
    key = os.getenv("GOOGLE_API_KEY")
    print(f"GOOGLE_API_KEY value from os.getenv: '{key}'")
    
    if key:
        print(f"Key length: {len(key)}")
        if key.startswith("AIza"):
            print("Key looks valid (starts with AIza)")
        else:
            print("Key format warning: Does not start with AIza")
    else:
        print("Key is None or Empty")
        
    print("--- Diagnostic End ---")

if __name__ == "__main__":
    test_loading()
