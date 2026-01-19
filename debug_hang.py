from backend.llm_analyzer import LLMAnalyzer
import time
import os

print("--- Debugging Connection Hang ---")
start_time = time.time()

try:
    analyzer = LLMAnalyzer()
    # print(f"Model: {analyzer.llm.model_name}")
    print("Sending Ping...")
    
    # We use the internal call to see the logs/behavior
    # We will override the logger to print to stdout if possible, but the class uses its own logger.
    # We just rely on stdout from the script.
    
    res = analyzer._call_llm("Ping", retries=3) # Reduced retries for debug
    
    elapsed = time.time() - start_time
    print(f"✅ Response received in {elapsed:.2f}s")
    print(f"Response: {res}")

except Exception as e:
    elapsed = time.time() - start_time
    print(f"❌ Failed after {elapsed:.2f}s. Error: {e}")
