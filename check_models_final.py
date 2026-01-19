from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from pathlib import Path
import os
import time

# Load env manually
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)
api_key = os.environ.get("GOOGLE_API_KEY")

CANDIDATES = [
    "gemini-1.5-flash",         # Standard
    "gemini-1.5-flash-001",     # Versioned
    "gemini-1.5-flash-002",     # Newer
    "gemini-1.5-flash-8b",      # Efficient
    "gemini-flash-latest",      # The one that worked (quota)
    "gemini-pro"                # Classic
]

print(f"--- STARTING FINAL MODEL CHECK (Key Len: {len(str(api_key))}) ---")

best_model = None

for model in CANDIDATES:
    print(f"\nTesting: {model}")
    try:
        llm = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            temperature=0.7
        )
        # Try to invoke
        start = time.time()
        res = llm.invoke("Hello")
        elapsed = time.time() - start
        
        print(f"✅ SUCCESS: {model} responded in {elapsed:.2f}s")
        print(f"Response: {res.content}")
        best_model = model
        break # STOP AT FIRST SUCCESS
        
    except Exception as e:
        error = str(e)
        if "404" in error:
            print(f"❌ 404 NOT FOUND: {model}")
        elif "429" in error or "RESOURCE_EXHAUSTED" in error:
            print(f"⚠️ QUOTA EXHAUSTED: {model}")
        else:
            print(f"❌ ERROR: {model} - {error}")

if best_model:
    print(f"\n🏆 WINNER: {best_model}")
else:
    print("\n💀 ALL MODELS FAILED")
