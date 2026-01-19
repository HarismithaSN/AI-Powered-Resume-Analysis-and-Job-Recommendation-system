import os
import time
import random
import logging
import json
from datetime import datetime, timedelta
import re
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from backend.llm_analyzer import LLMAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LinkedInScraper:
    def __init__(self, headless=False):
        """
        Initialize the LinkedIn Scraper.
        
        Args:
            headless (bool): Run browser in headless mode if True.
        """
        load_dotenv()
        self.email = os.getenv("LINKEDIN_EMAIL")
        self.password = os.getenv("LINKEDIN_PASSWORD")
        self.headless = headless
        self.driver = None
        self.llm_analyzer = LLMAnalyzer()
        
        if not self.email or not self.password:
            logger.warning("LinkedIn credentials not found in environment variables.")

    def setup_driver(self):
        """Sets up the Chrome WebDriver with options."""
        chrome_options = Options()
        if self.headless:
            # chrome_options.add_argument("--headless") # Commented out for now to see what's happening if needed, or re-enable
            pass
        
        # Anti-detection options
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("window-size=1920,1080")
        chrome_options.add_argument("--start-maximized")
        
        # Random user agent
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36"
        ]
        chrome_options.add_argument(f"user-agent={random.choice(user_agents)}")
        
        try:
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            logger.info("WebDriver initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise

    def wait_random(self, min_time=2, max_time=5):
        """Waits for a random amount of time to mimic human behavior."""
        time.sleep(random.uniform(min_time, max_time))

    def convert_posted_date(self, relative_date_str):
        """Converts relative date string (e.g., '2 days ago') to ISO date."""
        if not relative_date_str:
            return None
            
        relative_date_str = relative_date_str.lower().strip()
        now = datetime.now()
        
        try:
            if "minute" in relative_date_str or "hour" in relative_date_str or "just now" in relative_date_str:
                return now.isoformat()
            
            match = re.search(r"(\d+)", relative_date_str)
            if not match:
                return now.isoformat() # Fallback
                
            value = int(match.group(1))
            
            if "day" in relative_date_str:
                date = now - timedelta(days=value)
            elif "week" in relative_date_str:
                date = now - timedelta(weeks=value)
            elif "month" in relative_date_str:
                date = now - timedelta(days=value*30)
            else:
                date = now
                
            return date.isoformat()
        except Exception:
            return now.isoformat()

    def search_jobs(self, keywords, location, date_posted=None, experience_level=None, job_type=None, remote=None):
        """
        Navigates to LinkedIn jobs page and searches for jobs with filters.
        
        Args:
            keywords (str): Job title or keywords.
            location (str): Location.
            date_posted (str): '24h', 'week', 'month'.
            experience_level (str): 'internship', 'entry', 'associate', 'mid-senior', 'director'.
            job_type (str): 'full-time', 'part-time', 'contract', 'temp'.
            remote (bool): True for remote only.
        """
        if not self.driver:
            self.setup_driver()

        logger.info(f"Searching for: {keywords} in {location}")
        
        base_url = "https://www.linkedin.com/jobs/search/?"
        params = [
            f"keywords={keywords}",
            f"location={location}",
            "generateRedirectToLinkedInUrl=true"
        ]
        
        # Map filters to LinkedIn URL params
        if date_posted:
            mapping = {'24h': 'r86400', 'week': 'r604800', 'month': 'r2592000'}
            if val := mapping.get(date_posted.lower()):
                params.append(f"f_TPR={val}")
                
        if experience_level:
            # Simplified mapping
            mapping = {'internship': '1', 'entry': '2', 'associate': '3', 'mid-senior': '4', 'director': '5'}
            if val := mapping.get(experience_level.lower()):
                params.append(f"f_E={val}")
        
        if job_type:
            mapping = {'full-time': 'F', 'part-time': 'P', 'contract': 'C', 'temp': 'T'}
            if val := mapping.get(job_type.lower()):
                params.append(f"f_JT={val}")
                
        if remote:
             params.append("f_WT=2")
             
        search_url = base_url + "&".join(params)
        logger.info(f"Navigating to: {search_url}")
        
        try:
            self.driver.get(search_url)
            self.wait_random(3, 5)
        except Exception as e:
            if "invalid session id" in str(e).lower():
                logger.warning("Session invalid. Re-initializing driver...")
                self.setup_driver()
                self.driver.get(search_url)
                self.wait_random(3, 5)
            else:
                raise e
        
        return True

    def scrape_jobs_listing(self, limit_pages=3):
        """
        Scrapes job cards handling infinite scroll and pagination.
        Returns a list of dictionaries with basic job info.
        """
        logger.info(f"Scraping job listings (Limit: {limit_pages} pages/scrolls)...")
        job_data = []
        seen_urls = set()
        
        for page in range(limit_pages):
            logger.info(f"Scraping page/scroll {page + 1}/{limit_pages}...")
            
            # Scroll to bottom to trigger load
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self.wait_random(2, 4)
            
            # Check for "See more jobs" button and click it if exists
            try:
                see_more_btn = self.driver.find_element(By.CSS_SELECTOR, "button.infinite-scroller__show-more-button")
                if see_more_btn.is_displayed():
                    self.driver.execute_script("arguments[0].click();", see_more_btn)
                    self.wait_random(2, 4)
            except NoSuchElementException:
                pass # No button, might just be scroll
                
            # Find job cards
            # Selectors for the public job search page
            job_cards = self.driver.find_elements(By.CSS_SELECTOR, "div.base-card")
            if not job_cards:
                 job_cards = self.driver.find_elements(By.CSS_SELECTOR, "li.jobs-search-results__list-item")
            
            logger.info(f"Found {len(job_cards)} cards so far.")
            
            for card in job_cards:
                try:
                    # Public view selectors
                    link_elem = card.find_element(By.CSS_SELECTOR, "a.base-card__full-link")
                    job_url = link_elem.get_attribute("href")
                    
                    # Remove tracking parameters for cleaner URL
                    job_url = job_url.split('?')[0]
                    
                    if job_url in seen_urls:
                        continue
                    seen_urls.add(job_url)
                    
                    # --- Logic to extract Title, Company, Location ---
                    # Helper function to try multiple selectors
                    def get_text_safe(element, selectors):
                        for sel in selectors:
                            try:
                                el = element.find_element(By.CSS_SELECTOR, sel)
                                txt = el.text.strip()
                                if not txt:
                                     txt = el.get_attribute("innerText").strip()
                                if txt:
                                    return txt
                            except:
                                continue
                        return ""

                    # Selectors for Title
                    title = get_text_safe(card, [
                        ".base-search-card__title", 
                        ".job-card-list__title", 
                        "h3", 
                        ".artdeco-entity-lockup__title"
                    ])
                    
                    # Selectors for Company
                    company = get_text_safe(card, [
                        ".base-search-card__subtitle", 
                        ".job-card-container__company-name", 
                        ".artdeco-entity-lockup__subtitle", 
                        "h4"
                    ])
                    
                    # Selectors for Location
                    location = get_text_safe(card, [
                        ".job-search-card__location", 
                        ".job-card-container__metadata-item", 
                        ".artdeco-entity-lockup__caption"
                    ])

                    # Extract date
                    try:
                        date_elem = card.find_element(By.CSS_SELECTOR, "time")
                        date_text = date_elem.get_attribute("datetime") or date_elem.text.strip()
                        posted_date = self.convert_posted_date(date_text)
                    except NoSuchElementException:
                        posted_date = datetime.now().isoformat()

                    job_info = {
                        "job_title": title,
                        "company_name": company, # No longer empty
                        "location": location,
                        "job_url": job_url,
                        "posted_date": posted_date
                    }
                    
                    if not title:
                         logger.warning(f"Skipping card with missing title: {job_url}")
                         continue
                         
                    job_data.append(job_info)
                    
                except Exception as e:
                    logger.warning(f"Error parsing card: {e}")
                    continue # Skip incomplete or stale cards
            
            # Break if no new jobs found in a scroll (simple heuristic)
            if len(job_cards) == 0:
                break
                
        logger.info(f"Total unique jobs found: {len(job_data)}")
        return job_data

    def get_job_details_and_parse(self, job_url):
        """
        Navigates to a specific job URL, extracts details, and parses with LLM.
        """
        logger.info(f"Getting details for: {job_url}")
        try:
            self.driver.get(job_url)
            self.wait_random(2, 4)
            
            details = {}
            
            # --- Extraction ---
            try:
                # Public job page selector
                # Click "Show more" if description is collapsed
                try:
                    show_more_btn = self.driver.find_element(By.CSS_SELECTOR, "button.show-more-less-html__button--more")
                    show_more_btn.click()
                    self.wait_random(1, 2)
                except:
                    pass

                description_box = self.driver.find_element(By.CSS_SELECTOR, ".show-more-less-html__markup")
                description_html = description_box.get_attribute("innerHTML")
                description_text = description_box.text
                
                details["job_description"] = description_html
                
                # Applicants
                try:
                    applicants = self.driver.find_element(By.CSS_SELECTOR, ".num-applicants__caption").text.strip()
                    details["applicants_count"] = applicants
                except:
                    details["applicants_count"] = None
                    
            except Exception as e:
                logger.warning(f"Failed to extract basic details: {e}")
                return None # Critical failure
            
            # --- LLM Parsing ---
            logger.info("Parsing description with LLM...")
            parsed_data = self.llm_analyzer.parse_job_description(description_text[:2000]) # Limit chars for API
            
            if parsed_data and "error" not in parsed_data:
                details["salary_range"] = parsed_data.get("salary_range")
                details["required_skills"] = parsed_data.get("required_skills", [])
                details["job_type"] = parsed_data.get("job_type")
                # details["experience_level"] = parsed_data.get("experience_level")
            else:
                logger.warning("LLM parsing failed or returned error.")
                
            return details
            
        except Exception as e:
            logger.error(f"Error processing job {job_url}: {e}")
            return None

    def close(self):
        """Closes the browser instance."""
        if self.driver:
            self.driver.quit()
            logger.info("Browser closed.")

def generate_search_query(user_profile: dict, resume_keywords: list = None) -> str:
    """
    Builds a search query string based on user profile and resume data.
    """
    query_parts = []
    
    # 1. Job Title / Role
    # If explicit target role exists in profile, use it. Otherwise infer or use generic.
    if user_profile.get("target_role"):
         query_parts.append(user_profile["target_role"])
    elif resume_keywords:
        # Use top 1-2 keywords which might be titles
        query_parts.extend(resume_keywords[:1])
    
    # 2. Skills
    # Add top 2 skills
    if resume_keywords:
        # Assuming resume_keywords are mixed title/skills, take next few
        query_parts.extend(resume_keywords[1:3])
        
    return " ".join(query_parts) if query_parts else "Software Engineer"


from utils.database import save_job_recommendation, get_user_by_email, create_user

if __name__ == "__main__":
    # Test Script
    scraper = LinkedInScraper(headless=True) # Visible for testing
    try:
        scraper.setup_driver()
        
        # 1. Search
        scraper.search_jobs("Python Developer", "New York")
        
        # 2. Scrape List
        jobs = scraper.scrape_jobs_listing(limit_pages=1) # Just 1 page for test
        print(f"Scraped {len(jobs)} jobs.")
        
        # 3. Setup Test User
        test_email = "test_scraper@example.com"
        user = get_user_by_email(test_email)
        if not user:
            create_user("Test Scraper", test_email, "password123")
            user = get_user_by_email(test_email)
        user_id = user['user_id']
        
        # 4. Details & Save
        for i, job in enumerate(jobs[:3]): # Process top 3
            print(f"Processing ({i+1}/3): {job['job_title']}")
            details = scraper.get_job_details_and_parse(job['job_url'])
            
            if details:
                job.update(details)
                
                # Save
                save_job_recommendation(
                    user_id=user_id,
                    job_title=job['job_title'],
                    company_name=job['company_name'],
                    location=job['location'],
                    job_description=job.get('job_description', ''),
                    job_url=job['job_url'],
                    match_percentage=0.0,
                    posted_date=job.get('posted_date'),
                    salary_range=job.get('salary_range'),
                    applicants_count=job.get('applicants_count'),
                    required_skills=job.get('required_skills'),
                    job_type=job.get('job_type')
                )
                print("Saved to DB!")
            else:
                print("Skipped due to error.")
                
    except Exception as e:
        print(f"Fatal Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        scraper.close()
