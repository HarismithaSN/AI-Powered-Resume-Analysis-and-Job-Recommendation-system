from backend.llm_analyzer import LLMAnalyzer
import logging

# Setup logging to see the output
logging.basicConfig(level=logging.INFO)

def test_gemini_response():
    print("--- Starting JSON Debug Test ---")
    analyzer = LLMAnalyzer()
    
    dummy_resume = """
    Name: John Doe
    Email: john@example.com
    Skills: Python, Java, SQL
    Experience: 5 years at Tech Corp
    """
    
    prompt = """
    Analyze the resume.
    Return a JSON with:
    {
        "name": "string",
        "skills": ["list"]
    }
    """
    
    try:
        # Call the private method generic to get raw response handling logic
        # But wait, analyze_resume_generic handles the parsing. 
        # I want to see the RAW text before parsing.
        
        # We can call internal _call_llm directly
        raw_text = analyzer._call_llm(f"RESUME: {dummy_resume}\nTASK: {prompt}\nOUTPUT JSON ONLY")
        print("\n[RAW LLM RESPONSE START]")
        print(raw_text)
        print("[RAW LLM RESPONSE END]\n")
        
        # Now try the parser
        result = analyzer.analyze_resume_generic(dummy_resume, prompt)
        print("\n[PARSED RESULT]")
        print(result)
        
    except Exception as e:
        print(f"\n[ERROR] {e}")

if __name__ == "__main__":
    test_gemini_response()
