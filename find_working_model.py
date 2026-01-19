from backend.llm_analyzer import LLMAnalyzer
from langchain_google_genai import ChatGoogleGenerativeAI
import os
import sys

# Candidates to test (excluding known broken ones like 2.0-flash, 2.5-flash)
CANDIDATES = [
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash-lite-001",
    "gemini-pro-latest",
    "gemini-2.0-flash-exp" # Last resort
]

analyzer = LLMAnalyzer() # Just to load env

print("Starting Model Selection Test...")
working_model = None

for model in CANDIDATES:
    print(f"Testing model: {model}...")
    try:
        llm = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=os.environ["GOOGLE_API_KEY"],
            temperature=0.7
        )
        # Try a real invocation
        res = llm.invoke("Ping")
        print(f"✅ SUCCESS: {model} responded: {res.content}")
        working_model = model
        break
    except Exception as e:
        print(f"❌ FAILED: {model} - Error: {e}")

if working_model:
    print(f"RECOMMENDATION: Use '{working_model}'")
    # Save it to a temporary file so I can read it if needed, or just reading logs is fine
else:
    print("CRITICAL: No working models found.")
