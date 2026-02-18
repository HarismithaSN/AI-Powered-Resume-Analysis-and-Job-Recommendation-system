# 🚀 AI-Powered Resume Analysis & Intelligent Job Recommendation System

An AI-driven full-stack web application that analyzes resumes, identifies skill gaps, calculates ATS compatibility scores, and provides intelligent job recommendations using Large Language Models (LLMs).

> **Note:** This project was developed as part of the **Infosys Springboard Virtual Internship 6.0** (8-week program).

---

## 📌 About The Project
The system is designed to solve a critical real-world recruitment challenge: **manual resume screening and inefficient job matching.** Instead of traditional keyword matching, this platform uses structured AI analysis to provide:

* **Deep Insights:** Clear strength and weakness identification.
* **Granular Scoring:** Section-wise resume evaluation.
* **Growth Roadmap:** Skill gap detection and personalized learning suggestions.
* **Precision Matching:** Intelligent resume-to-job match percentages.

---

## ✨ Core Features
* **Secure Authentication:** User registration and login with `bcrypt` password hashing.
* **Flexible Uploads:** Support for both **PDF** and **DOCX** formats.
* **AI Analysis:** Deep content extraction using LangChain and LLMs.
* **ATS Scoring:** Compatibility calculation with section-wise breakdowns.
* **Skill Gap Analysis:** Advanced detection of missing skills based on target roles.
* **Dynamic Web Scraping:** Real-time job listings fetched via **Selenium**.
* **Smart Dashboard:** Personalized job recommendations and matching scores.

---

## 🛠 Tech Stack

| Component | Technology |
| :--- | :--- |
| **Frontend** | Streamlit |
| **Backend** | Python |
| **AI & NLP** | LangChain, Large Language Models (LLMs) |
| **Web Scraping** | Selenium |
| **Database** | MongoDB / SQLite |
| **Security** | Bcrypt (Password Hashing) |
| **File Processing** | PyPDF2, python-docx |

---
## 📸 Project Walkthrough

### 1. Welcome & Authentication
*The entry point of the application featuring secure user login and a clean interface.*
![Home Screen](./Screenshot/home.jpg)

### 2. Resume Parsing & ATS Analysis
*The AI extracts text from uploaded PDF/DOCX files and calculates an ATS compatibility score based on industry standards.*
![Resume Upload](./Screenshots/resume.jpg)
![Scoring Logic](./Screenshots%20ai/score.jpg)

### 3. Skill Gap Detection & Recommendations
*Detailed analysis of missing technical skills and soft skills, paired with personalized learning paths.*
![Skill Analysis](./Screenshots%20ai/skill.jpg)
![Learning Path](./Screenshots%20ai/skill1.jpg)

### 4. Intelligent Job Recommendations
*Dynamic job scraping integrated with an LLM-powered matching engine to show the most relevant opportunities.*
![Job Recommendations](./Screenshots%20ai/job.jpg)
![Match Comparison](./Screenshots%20ai/com-j.jpg)

## ⚙️ How It Works



1.  **Auth:** User registers and logs in securely.
2.  **Upload:** User uploads a resume; the system extracts and cleans the text.
3.  **Analysis:** An LLM processes the content using **Structured Prompt Engineering**.
4.  **Generation:** The system generates a resume score, identifies strengths/weaknesses, and highlights skill gaps.
5.  **Matching:** Selenium scrapes job listings dynamically; the system calculates a relevance score.
6.  **Results:** Personalized job recommendations are displayed on the user dashboard.

---

## 🧠 Technical Highlights
* **Structured Prompt Engineering:** Ensures consistent and predictable AI outputs.
* **Scalability:** Uses JSON-based response parsing for easy data handling.
* **Algorithm Design:** Multi-factor weighted scoring for resume evaluation.
* **Robustness:** Implemented exception handling and retry logic for API stability.
* **Data Integrity:** Deduplication logic for scraped job listings and secure session management.

---

## 📈 Real-World Impact
* **For Candidates:** Strategically improves resume quality and bridges skill gaps with actionable advice.
* **For Recruiters:** Reduces manual workload through automated, objective evaluation.
* **For Education:** Provides a scalable way to offer career guidance and learning suggestions.

---

## 🎯 Key Learnings
* End-to-end AI-integrated full-stack development.
* Practical experience with **LangChain** workflows and LLM orchestration.
* Designing matching algorithms for unstructured data.
* Handling dynamic web content through automated scraping.

---

## 👩‍💻 Author
**Harismitha S N** *MCA Student | Dayananda Sagar College of Engineering* 
