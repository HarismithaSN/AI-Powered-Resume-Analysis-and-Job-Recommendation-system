from backend.llm_analyzer import LLMAnalyzer
import time

print("--- Verify Smart Retry Logic ---")

try:
    analyzer = LLMAnalyzer()
    # Explicitly test 1.5 pro
    from langchain_google_genai import ChatGoogleGenerativeAI
    import os
    analyzer.llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", google_api_key=os.environ["GOOGLE_API_KEY"])
    # print(f"Model: {analyzer.llm.model_name}")
    print("Sending Ping (Expect delay if Quota Exceeded)...")
    
    start = time.time()
    res = analyzer._call_llm("Ping", retries=2)
    elapsed = time.time() - start
    
    if res:
            print(f"✅ SUCCESS: Response received in {elapsed:.1f}s")
            print(f"Response: {res}")
    else:
            print(f"❌ FAIL: No response after {elapsed:.1f}s")

except Exception as e:
    print(f"❌ CRITICAL FAIL: {e}")
