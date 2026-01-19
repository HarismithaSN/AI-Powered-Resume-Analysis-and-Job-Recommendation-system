import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.llm_analyzer import LLMAnalyzer

def test_mock_response():
    print("Testing Mock Mode...")
    analyzer = LLMAnalyzer()
    analyzer.mock_mode = True
    
    results = analyzer.analyze_resume_comprehensive("Dummy Text")
    
    expected_keys = ["candidate_name", "candidate_email", "candidate_phone", "strengths", "weaknesses"]
    missing = [k for k in expected_keys if k not in results]
    
    if missing:
        print(f"FAILED: Missing keys: {missing}")
    else:
        print("SUCCESS: All keys present.")
        print(f"Name: {results['candidate_name']}")
        print(f"Strengths: {len(results['strengths'])}")

if __name__ == "__main__":
    test_mock_response()
