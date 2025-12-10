# Project Setup & Installation Guide (Milestone 1)

This document explains all installation steps and environment setup required for Milestone 1.  
A proper project setup ensures clean code organization, easy collaboration, secure file handling, and smooth development throughout the project lifecycle.

---

# 1. Install Python

Install **Python 3.9 or higher** from:

https://www.python.org/downloads/

During installation:
- ✔ Enable “Add Python to PATH”
- ✔ Use default installation options

---

# 2. Create Project Folder

Create a main project directory:
InfosysProject


Open the folder in **PyCharm**.

---

# 3. Create & Activate Virtual Environment

PyCharm creates a virtual environment automatically.

Or create manually:

python -m venv venv


Activate it on Windows:


A virtual environment ensures project dependencies stay isolated.

---

# 4. Install Required Python Libraries

Open the PyCharm terminal and run:

pip install streamlit
pip install PyPDF2
pip install python-docx
pip install bcrypt
pip install python-dotenv


These libraries are used for:
- Streamlit → frontend UI
- PyPDF2 → PDF text extraction
- python-docx → DOCX text extraction
- bcrypt → secure password hashing
- python-dotenv → loading sensitive environment variables

SQLite requires **no installation** because it's built into Python.

---

# 5. Create the Required Folder Structure

Your project must contain the following directories:



InfosysProject/
│── backend/
│── frontend/
│── utils/
│── data/
│ └── resumes/
│── .env
│── .gitignore
│── README.md


Each folder has a purpose:
- `backend/` → authentication, resume processing
- `frontend/` → Streamlit pages
- `utils/` → database utilities
- `data/resumes/` → uploaded resumes storage

---

# 6. Create .env File

Create a file named `.env` in the root folder:



SECRET_KEY=your_secret_here


This file stores sensitive information and must **never** be committed to Git.

---

# 7. Create .gitignore File

Add these lines inside `.gitignore`:



venv/
pycache/
.env
data/resumes/
*.db


This prevents sensitive and unnecessary files from being tracked in Git.

---

# 8. Initialize Git Repository (Optional but Recommended)

Run in PyCharm terminal:



git init


Git helps track changes and supports project collaboration.

---

# Why This Setup Matters

This setup ensures:
- ✔ Clean and organized codebase  
- ✔ Secure handling of passwords and environment variables  
- ✔ Easy teamwork in future milestones  
- ✔ Stable environment for backend, frontend, and AI components  
- ✔ Prevents version conflicts and dependency issues  

A properly configured environment forms the **foundation** for the entire project.

---

# 🎉 Deliverable (As Required in Milestone 1)

### ✔ Fully configured development environment  
### ✔ Organized folder structure created  
### ✔ All Python dependencies installed  
### ✔ README.md containing complete documented setup process  

This completes the installation and setup requirements for **Milestone 1**.


