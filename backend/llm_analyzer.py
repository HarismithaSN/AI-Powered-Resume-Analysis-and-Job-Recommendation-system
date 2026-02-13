import os
import logging
import json
import re
import time
import ast
from typing import Dict, Any, Optional
from pathlib import Path

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from google.api_core.exceptions import ResourceExhausted

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
logger.info(f"Loading .env from: {env_path} (Exists: {env_path.exists()})")
load_dotenv(dotenv_path=env_path, override=True)

class LLMAnalyzer:
    """
    Robust LLM Analyzer for Google Gemini.
    Handles JSON parsing with multiple fallback strategies.
    """

    def __init__(self, temperature: float = 0.5):
        """
        Initialize with lower temperature for more deterministic outputs.
        """
        self.mock_mode = False
        self.llm = None
        
        # 1. Get API Key
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key or "your_api_key" in api_key.lower() or len(api_key) < 20:
            api_key = self._recover_api_key_from_file()

        # 2. Initialize Gemini
        if not api_key:
            logger.warning("No valid GOOGLE_API_KEY found. Analysis will fail.")
            self.llm = None
        else:
            try:
                # Use gemini-flash-latest (Verified available)
                # Use gemini-1.5-flash (Standard stable model)
                self.llm = ChatGoogleGenerativeAI(
                    model="gemini-flash-latest",
                    google_api_key=api_key,
                    temperature=temperature,
                    convert_system_message_to_human=True,
                    request_timeout=60,
                    max_retries=2,
                    # Disable safety filters to prevent "Empty Response" on valid resumes
                    safety_settings={
                        "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
                        "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
                        "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
                        "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
                    }
                )
                logger.info("LLMAnalyzer initialized successfully with Gemini (gemini-1.5-flash).")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini: {e}")
                self.llm = None

    def _recover_api_key_from_file(self) -> Optional[str]:
        """Attempt to read GOOGLE_API_KEY directly from .env file as a fallback."""
        try:
            env_path = Path(__file__).parent.parent / ".env"
            if env_path.exists():
                logger.info(f"Attempting manual key recovery from {env_path}")
                content = env_path.read_text()
                for line in content.splitlines():
                    if line.strip().startswith("GOOGLE_API_KEY="):
                        parts = line.split("=", 1)
                        if len(parts) == 2:
                            key = parts[1].strip().strip('"').strip("'")
                            if len(key) > 20:
                                os.environ["GOOGLE_API_KEY"] = key
                                return key
        except Exception:
            pass
        return None

    def _clean_and_parse_json(self, text: str) -> Dict[str, Any]:
        """
        Robust JSON parsing strategy:
        1. Clean Markdown fences.
        2. Try standard json.loads.
        3. Try regex extraction of first {...}.
        4. Try ast.literal_eval (handling single quotes).
        """
        if not text:
            return {"error": "Empty response from LLM"}

        # 1. Basic cleaning
        text = text.strip()
        # Remove markdown fences
        if "```" in text:
            # Try to match specific json blocks first
            if "```json" in text:
                try:
                    text = text.split("```json")[1].split("```")[0].strip()
                except IndexError:
                    pass
            else:
                try:
                    text = text.split("```")[1].split("```")[0].strip()
                except IndexError:
                    pass

        # 2. Direct JSON Parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass # Fallthrough

        # 3. Regex Extraction (Find outermost brackets)
        try:
            match = re.search(r"(\{.*\})", text, re.DOTALL)
            if match:
                potential_json = match.group(1)
                return json.loads(potential_json)
        except json.JSONDecodeError:
            pass

        # 4. AST Literal Eval (Handles Python-style dicts with single quotes)
        try:
            # Need to find start/end again for this to work well
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                potential_dict = text[start:end+1]
                return ast.literal_eval(potential_dict)
        except (ValueError, SyntaxError):
            pass

        logger.error(f"Failed to parse JSON. Raw text start: {text[:200]}...")
        return {"error": "Invalid JSON response from LLM", "raw_response": text[:500]}

    def _call_llm(self, prompt: str, retries: int = 2) -> str:
        if not self.llm:
            print("ERR: LLM not initialized.")
            raise Exception("LLM is not initialized.")

        messages = [HumanMessage(content=prompt)]
        
        for attempt in range(retries + 1):
            try:
                print(f"DEBUG: Calling Gemini (Attempt {attempt+1})...")
                response = self.llm.invoke(messages)
                content = str(response.content)
                print(f"DEBUG: Response gathered. Length: {len(content)}")
                return content

            except Exception as e:
                print(f"DEBUG: LLM Error: {e}")
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    wait = 5.0 * (attempt + 1)
                    if wait > 30: wait = 30
                    logger.warning(f"Quota exceeded. Waiting {wait}s...")
                    time.sleep(wait)
                    continue
                
                logger.error(f"LLM Call Error: {e}")
                if attempt == retries:
                    raise e
                time.sleep(2)
        
        return ""

    def analyze_resume_generic(self, resume_text: str, task_prompt: str) -> Dict[str, Any]:
        if self.mock_mode:
            return self._get_mock_response(task_prompt)

        full_prompt = f"""
        You are an expert resume analyzer.
        RESUME TEXT:
        {resume_text}
        
        TASK:
        {task_prompt}
        
        CRITICAL OUTPUT INSTRUCTIONS:
        - Output ONLY valid JSON.
        - No markdown formatting.
        - No introductory text.
        - Ensure all strings are double-quoted.
        """

        try:
            response_text = self._call_llm(full_prompt)
            result = self._clean_and_parse_json(response_text)
            
            # FALLBACK: If API returns error/empty, fall back to mock data so user sees something
            if "error" in result:
                 print("DEBUG: API returned error, falling back to mock data.")
                 mock_res = self._get_mock_response(task_prompt, resume_text)
                 mock_res["summary"] += " [NOTE: Real AI analysis failed/timed out, showing demo data.]"
                 return mock_res
                 
            return result
        except Exception as e:
            print(f"DEBUG: Exception in analyze_resume_generic: {e}")
            # Fallback on crash
            mock_res = self._get_mock_response(task_prompt, resume_text)
            
            error_msg = str(e).lower()
            if "exhausted" in error_msg or "quota" in error_msg or "429" in error_msg:
                mock_res["summary"] += " [NOTE: Google AI Daily Quota reached. Showing provisional data. Real AI will return when quota resets.]"
            else:
                mock_res["summary"] += " [NOTE: AI Service temporarily unavailable. Showing provisional data.]"
            
            return mock_res

    # --- Specific Analysis Methods (Keep wrappers as they defines prompts) ---

    def analyze_resume_comprehensive(self, resume_text: str) -> Dict[str, Any]:
        logger.info(f"Analyzing resume text (Length: {len(resume_text)} characters)")
        if len(resume_text) < 50:
            logger.warning("Resume text is suspiciously short/empty!")
            return {"error": "Resume content appears to be empty or unreadable. Please upload a clear text-based PDF/DOCX."}

        prompt = """
        Review the resume and provide a comprehensive, critical analysis aimed at a Software Engineering/Tech role.
        
        CRITICALLY ANALYZE FOR GAPS:
        1. **Internships/Work Experience**: Does the candidate have industry experience? If missing, this is a CRITICAL GAP.
        2. **DSA & Problem Solving**: Look specifically for "Data Structures", "Algorithms", "LeetCode", "CodeForces", etc. If missing, suggest it.
        3. **Project Complexity**: Are the projects simple or complex? (e.g., clone apps vs real-world solutions).
        4. **Tech Stack**: Is the stack modern? (e.g., React, Node, Cloud vs legacy).

        Return a JSON object with this exact structure:
        {
            "candidate_name": "Name or 'Not Found'",
            "candidate_email": "Email or 'Not Found'",
            "candidate_phone": "Phone or 'Not Found'",
            "score": INTEGER_0_TO_100,
            "summary": "Brief professional summary. Mention if they differ from a typical candidate (e.g. no internships).",
            "strengths": ["List of 3-5 key strengths (e.g. 'Strong Academic Record', 'Full Stack Projects')"],
            "weaknesses": [
                "List of 3-5 critical weaknesses.",
                "Explicitly mention 'Missing Internship Experience' if applicable.",
                "Explicitly mention 'Lack of DSA/Competitive Programming evidence' if applicable."
            ],
            "skills_found": ["List of technical/soft skills"],
            "missing_skills": ["List of missing implied skills (e.g., Git, Docker, Testing)"],
            "improvement_suggestions": [
                {"impact": "High", "suggestion": "Specific advice (e.g. 'Focus on DSA questions on LeetCode')"},
                {"impact": "High", "suggestion": "Advice on Internships if missing"},
                {"impact": "Medium", "suggestion": "Advice on Projects/Certs"}
            ],
            "section_analysis": {
                "summary_section": {"score": INT, "feedback": ["feedback"]},
                "experience_section": {"score": INT, "feedback": ["feedback"]},
                "projects_section": {"score": INT, "feedback": ["feedback"]},
                "skills_section": {"score": INT, "feedback": ["feedback"]},
                "education_section": {"score": INT, "feedback": ["feedback"]}
            }
        }
        """
        return self.analyze_resume_generic(resume_text, prompt)

    def analyze_job_recommendations(self, resume_text: str) -> Dict[str, Any]:
        prompt = """
        Recommend 3-5 job roles based on the resume.
        Return JSON:
        {
            "recommendations": [
                {
                    "role": "Job Title",
                    "match_score": INT_0_TO_100,
                    "matching_skills": ["skill1", "skill2"],
                    "missing_skills": ["skill3", "skill4"],
                    "salary_range": "e.g. $80k - $100k"
                }
            ],
            "overall_summary": "Brief summary of career path"
        }
        """
        return self.analyze_resume_generic(resume_text, prompt)

    def parse_job_description(self, job_description: str) -> Dict[str, Any]:
        prompt = f"""
        Extract structured data from this Job Description:
        {job_description}
        
        Return JSON:
        {{
            "salary_range": "string or null",
            "required_skills": ["list"],
            "experience_level": "string",
            "job_type": "string",
            "education": "string"
        }}
        """
        # Note: replace prompt template usage with f-string for simplicity in generic call if needed, 
        # but here we pass description in prompt.
        return self.analyze_resume_generic("", prompt) 

    def analyze_match_weighted(self, resume_text: str, job_description: str) -> Dict[str, Any]:
        """
        Analyzes match with specific weighted scoring:
        - Skills: 50%
        - Experience: 25%
        - Education: 15%
        - Responsibility: 10%
        """
        if self.mock_mode:
            return {
                "match_score": 85,
                "matching_skills": ["Python", "Streamlit"],
                "missing_skills": ["Java"],
                "analysis_summary": "Good match based on mock data.",
                "explanation": "Mock explanation."
            }

        prompt = f"""
        Compare the Resume and Job Description using the following STRICT SCORING RULES:
        
        1. **Skill Match (50%)**: Do they have the required technical/soft skills?
        2. **Experience Match (25%)**: Do they have the years of experience and relevant industry background?
        3. **Education Match (15%)**: Do they meet the degree/field requirements?
        4. **Responsibility Match (10%)**: Have they done similar tasks?

        RESUME:
        {resume_text[:4000]}
        
        JOB DESCRIPTION:
        {job_description[:4000]}
        
        Return a JSON object with this exact structure:
        {{
            "match_score": INT_0_TO_100 (Sum of weighted components),
            "component_scores": {{
                "skills": INT_0_TO_50,
                "experience": INT_0_TO_25,
                "education": INT_0_TO_15,
                "responsibility": INT_0_TO_10
            }},
            "matching_skills": ["list of matched skills"],
            "missing_skills": ["list of missing skills"],
            "analysis_summary": "Brief explanation of the score."
        }}
        """
        return self.analyze_resume_generic(resume_text, prompt)

    def analyze_match(self, resume_text: str, job_description: str) -> Dict[str, Any]:
        # Alias for backward compatibility or simple match
        return self.analyze_match_weighted(resume_text, job_description)

    def analyze_skills_gap(self, resume_text: str, target_role: str, experience_level: str) -> Dict[str, Any]:
        prompt = f"""
        Perform a comprehensive gap analysis between the Resume and the Target Role: "{target_role}" ({experience_level}).
        
        RESUME:
        {resume_text[:4000]}
        
        Return a JSON object with this exact structure:
        {{
            "match_score": INT_0_TO_100,
            "summary": "Brief assessment of readiness for this specific role/level.",
            "must_have": {{
                "matched": ["list of matched critical skills found in resume"],
                "missing": ["list of missing critical skills required for the role"]
            }},
            "nice_to_have": {{
                "matched": ["list of matched bonus skills"],
                "missing": ["list of missing bonus skills"]
            }},
            "recommendations": [
                {{
                    "skill": "Skill Name",
                    "why_important": "Reason why this is critical for {target_role}",
                    "learning_resources": ["Specific Topic 1", "Specific Topic 2"]
                }}
            ]
        }}
        """
        return self.analyze_resume_generic(resume_text, prompt)

    def check_connection(self) -> bool:
        if self.mock_mode: return False
        try:
            # Simple ping
            self._call_llm("Respond with 'pong'", retries=0)
            return True
        except Exception:
            return False

    def _extract_details_via_regex(self, text: str) -> Dict[str, str]:
        """Fallback method to extract basic details when LLM fails."""
        details = {}
        
        # Email
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        details["email"] = email_match.group(0) if email_match else "Not Found"
        
        # Phone (Simple approximation)
        phone_match = re.search(r'(\+\d{1,3}[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}', text)
        details["phone"] = phone_match.group(0) if phone_match else "Not Found"
        
        # Name (Heuristic: First non-empty line that isn't a label)
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        # Skip common headers if they appear first
        skip_words = ["resume", "curriculum", "vitae", "cv", "bio", "profile"]
        for line in lines[:5]:
            if len(line.split()) < 5 and line.lower() not in skip_words: # Names are usually short
                 details["name"] = line.title()
                 break
        details["name"] = details.get("name", "Candidate")
        
        return details

    def _get_mock_response(self, task_prompt: str, resume_text: str = "") -> Dict[str, Any]:
        # Try to extract real details if resume_text is provided
        real_details = {"name": "Mock User", "email": "mock@example.com", "phone": "123-456-7890"}
        if resume_text:
            extracted = self._extract_details_via_regex(resume_text)
            real_details["name"] = extracted.get("name", "Mock User")
            real_details["email"] = extracted.get("email", "mock@example.com")
            real_details["phone"] = extracted.get("phone", "123-456-7890")

        # Detect if this is a Skills Gap Analysis request
        if "gap analysis" in task_prompt.lower() or "target role" in task_prompt.lower():
            return {
                "match_score": 65,
                "summary": "Partial Analysis (AI Unavailable): Resume detected, but advanced matching failed. Showing estimated gaps.",
                "must_have": {
                    "matched": ["Python", "Basic SQL", "Communication"],
                    "missing": ["Advanced System Design", "Kubernetes", "GraphQL"]
                },
                "nice_to_have": {
                    "matched": ["Git"],
                    "missing": ["Cloud Certifications", "Mentoring"]
                },
                "recommendations": [
                    {
                        "skill": "System Design",
                        "why_important": "Critical for senior roles.",
                        "learning_resources": ["System Design Primer", "High Scalability Blog"]
                    },
                    {
                        "skill": "Kubernetes",
                        "why_important": "Essential for modern deployment.",
                        "learning_resources": ["K8s Documentation", "Udemy K8s Course"]
                    }
                ]
            }
        
        # Default to Resume Analysis structure
        return {
            "candidate_name": real_details["name"],
            "candidate_email": real_details["email"],
            "candidate_phone": real_details["phone"],
            "score": 85,
            "summary": "This is a provisional report generated because the AI service is momentarily busy. Basic details extracted.",
            "strengths": ["Demonstrates technical potential", "Clear document structure", "Identifiable contact information"],
            "weaknesses": ["Detailed AI content analysis paused (Quota Limit)", "Specific skill proficiency could not be verified"],
            "skills_found": ["Python", "Technical Skills (General)"],
            "improvement_suggestions": [
                {"impact": "High", "suggestion": "Retry analysis in a few minutes for full AI insights."},
                {"impact": "Medium", "suggestion": "Ensure resume formatting is standard."}
            ],
            "section_analysis": {
                "summary_section": {"score": 8, "feedback": ["Section detected."]},
                "experience_section": {"score": 7, "feedback": ["Experience section identified."]},
                "projects_section": {"score": 9, "feedback": ["Projects listed."]},
                "skills_section": {"score": 8, "feedback": ["Skills found."]},
                "education_section": {"score": 9, "feedback": ["Education details present."]}
            }
        }

if __name__ == "__main__":
    try:
        analyzer = LLMAnalyzer()
        if analyzer.check_connection():
            print("Connection Verified.")
        else:
            print("Connection Failed.")
    except Exception as e:
        print(f"Error: {e}")
