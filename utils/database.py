# utils/database.py
import sqlite3
import os
import re
import json
from datetime import datetime
import bcrypt

# -----------------------------
# Helpers / Validation
# -----------------------------
EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w{2,}$")
URL_REGEX = re.compile(
    r'^(https?:\/\/)?'
    r'([A-Za-z0-9-]+\.)+[A-Za-z]{2,6}'
    r'(\/[\w\-\._~:\/?#[\]@!$&\'()*+,;=%]*)?$'
)

def is_valid_email(email: str) -> bool:
    return bool(EMAIL_REGEX.match(email or ""))

def is_valid_url(url: str) -> bool:
    return bool(URL_REGEX.match(url or ""))

def iso_now() -> str:
    return datetime.utcnow().isoformat()

def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(
        plain_password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

def check_password(plain_password: str, hashed: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed.encode("utf-8")
    )

# -----------------------------
# Create data folder & connect
# -----------------------------
DB_DIR = "data"
DB_FILE = os.path.join(DB_DIR, "app.db")

if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cur = conn.cursor()

# -----------------------------
# Create tables
# -----------------------------
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    registration_date TEXT NOT NULL,
    resume_file_path TEXT,
    college_name TEXT,
    course TEXT,
    graduation_year TEXT
)
""")
# Try to add new columns if upgrading from older DB
import sqlite3 as _sqlite3  # at top you already imported sqlite3; reuse if needed

for col_def in [
    "college_name TEXT",
    "course TEXT",
    "graduation_year TEXT",
    "current_role TEXT",
    "experience_years TEXT"
]:
    col_name = col_def.split()[0]
    try:
        # Check if column already exists
        cur.execute("PRAGMA table_info(users)")
        existing_cols = [r[1] for r in cur.fetchall()]
        if col_name not in existing_cols:
            cur.execute(f"ALTER TABLE users ADD COLUMN {col_def}")
    except _sqlite3.OperationalError:
        # Ignore if something fails; table will be recreated only in dev
        pass

for col_def in [
    "posted_date TEXT",
    "posted_date TEXT",
    "salary_range TEXT",
    "applicants_count TEXT",
    "required_skills TEXT", 
    "job_type TEXT",
    "matching_skills TEXT",
    "missing_skills TEXT",
    "analysis_summary TEXT",
    "component_scores TEXT",
    "status TEXT"
]:
    col_name = col_def.split()[0]
    try:
        # Check if column already exists
        cur.execute("PRAGMA table_info(job_recommendations)")
        rows = cur.fetchall()
        # If table doesn't exist yet, fetchall returns empty list, loop won't run, which is fine
        if rows:
            existing_cols = [r[1] for r in rows]
            if col_name not in existing_cols:
                cur.execute(f"ALTER TABLE job_recommendations ADD COLUMN {col_def}")
    except _sqlite3.OperationalError:
        pass


cur.execute("""
CREATE TABLE IF NOT EXISTS resume_analysis (
    analysis_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    extracted_resume_text TEXT,
    analysis_scores TEXT,
    strengths TEXT,
    weaknesses TEXT,
    identified_skills TEXT,
    recommended_skills TEXT,
    analysis_timestamp TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS job_recommendations (
    job_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    job_title TEXT,
    company_name TEXT,
    location TEXT,
    job_description TEXT,
    job_url TEXT,
    match_percentage REAL,
    scraping_date TEXT,
    posted_date TEXT,
    salary_range TEXT,
    applicants_count TEXT,
    required_skills TEXT,
    job_type TEXT,
    status TEXT DEFAULT 'new',
    FOREIGN KEY (user_id) REFERENCES users(user_id)
)
""")

# Indexes
cur.execute("CREATE INDEX IF NOT EXISTS idx_user_email ON users(email)")
cur.execute("CREATE INDEX IF NOT EXISTS idx_resume_user ON resume_analysis(user_id)")
cur.execute("CREATE INDEX IF NOT EXISTS idx_jobs_user ON job_recommendations(user_id)")
conn.commit()

# -----------------------------
# CRUD: Users
# -----------------------------
def create_user(
    name: str,
    email: str,
    plain_password: str,
    registration_date: str = None,
    resume_path: str = None,
    college_name: str = None,
    course: str = None,
    graduation_year: str = None,
    current_role: str = None,
    experience_years: str = None,
) -> dict:
    if not name or not name.strip():
        return {"success": False, "error": "Name is required."}
    if not is_valid_email(email):
        return {"success": False, "error": "Invalid email format."}
    if not plain_password or len(plain_password) < 8:
        return {"success": False, "error": "Password must be at least 8 characters."}

    registration_date = registration_date or iso_now()
    hashed = hash_password(plain_password)

    try:
        cur.execute(
            """
            INSERT INTO users
            (name, email, hashed_password, registration_date,
             resume_file_path, college_name, course, graduation_year, current_role, experience_years)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name.strip(),
                email.strip().lower(),
                hashed,
                registration_date,
                resume_path,
                (college_name or "").strip() or None,
                (course or "").strip() or None,
                (graduation_year or "").strip() or None,
                (current_role or "").strip() or None,
                (experience_years or "").strip() or None,
            ),
        )
        conn.commit()
        return {"success": True, "user_id": cur.lastrowid}
    except sqlite3.IntegrityError:
        return {"success": False, "error": "Email already exists."}

def get_user_by_email(email: str):
    cur.execute(
        """
        SELECT user_id, name, email, registration_date,
               resume_file_path, college_name, course, graduation_year, current_role, experience_years
        FROM users WHERE email = ?
        """,
        (email.strip().lower(),),
    )
    row = cur.fetchone()
    if not row:
        return None
    keys = (
        "user_id",
        "name",
        "email",
        "registration_date",
        "resume_file_path",
        "college_name",
        "course",
        "graduation_year",
        "current_role",
        "experience_years"
    )
    return dict(zip(keys, row))

def get_user_with_password(email: str):
    cur.execute(
        """
        SELECT user_id, name, email, hashed_password,
               registration_date, resume_file_path,
               college_name, course, graduation_year
        FROM users WHERE email = ?
        """,
        (email.strip().lower(),),
    )
    row = cur.fetchone()
    if not row:
        return None
    keys = (
        "user_id",
        "name",
        "email",
        "hashed_password",
        "registration_date",
        "resume_file_path",
        "college_name",
        "course",
        "graduation_year",
    )
    return dict(zip(keys, row))

def update_user(user_id: int, **fields):
    allowed = {
        "name",
        "resume_file_path",
        "course",
        "graduation_year",
        "current_role",
        "experience_years",
    }
    updates = []
    params = []
    for k, v in fields.items():
        if k in allowed:
            updates.append(f"{k} = ?")
            params.append(v)
    if not updates:
        return {"success": False, "error": "No updatable fields provided."}

    params.append(user_id)
    sql = f"UPDATE users SET {', '.join(updates)} WHERE user_id = ?"
    cur.execute(sql, tuple(params))
    conn.commit()
    return {"success": True, "updated": cur.rowcount}

def delete_user(user_id: int):
    cur.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    conn.commit()
    return {"success": True, "deleted": cur.rowcount}

# -----------------------------
# CRUD: Resume Analysis
# -----------------------------
def save_resume_analysis(
    user_id: int,
    extracted_text: str,
    analysis_scores: dict = None,
    strengths: list = None,
    weaknesses: list = None,
    identified_skills: list = None,
    recommended_skills: list = None,
    analysis_timestamp: str = None,
) -> dict:
    cur.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
    if cur.fetchone() is None:
        return {"success": False, "error": "User does not exist."}

    analysis_timestamp = analysis_timestamp or iso_now()
    cur.execute(
        """
        INSERT INTO resume_analysis
        (user_id, extracted_resume_text, analysis_scores, strengths,
         weaknesses, identified_skills, recommended_skills, analysis_timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            extracted_text,
            json.dumps(analysis_scores or {}),
            json.dumps(strengths or []),
            json.dumps(weaknesses or []),
            json.dumps(identified_skills or []),
            json.dumps(recommended_skills or []),
            analysis_timestamp,
        ),
    )
    conn.commit()
    return {"success": True, "analysis_id": cur.lastrowid}

def get_resume_analysis_by_user(user_id: int):
    cur.execute(
        "SELECT * FROM resume_analysis WHERE user_id = ? ORDER BY analysis_timestamp DESC",
        (user_id,),
    )
    rows = cur.fetchall()
    results = []
    for r in rows:
        results.append(
            {
                "analysis_id": r[0],
                "user_id": r[1],
                "extracted_resume_text": r[2],
                "analysis_scores": json.loads(r[3]) if r[3] else {},
                "strengths": json.loads(r[4]) if r[4] else [],
                "weaknesses": json.loads(r[5]) if r[5] else [],
                "identified_skills": json.loads(r[6]) if r[6] else [],
                "recommended_skills": json.loads(r[7]) if r[7] else [],
                "analysis_timestamp": r[8],
            }
        )
    return results

def update_resume_analysis(analysis_id: int, **fields):
    allowed = {
        "extracted_resume_text",
        "analysis_scores",
        "strengths",
        "weaknesses",
        "identified_skills",
        "recommended_skills",
        "analysis_timestamp",
    }
    updates = []
    params = []
    for k, v in fields.items():
        if k in allowed:
            if isinstance(v, (dict, list)):
                v = json.dumps(v)
            updates.append(f"{k} = ?")
            params.append(v)
    if not updates:
        return {"success": False, "error": "No valid fields to update."}

    params.append(analysis_id)
    sql = f"UPDATE resume_analysis SET {', '.join(updates)} WHERE analysis_id = ?"
    cur.execute(sql, tuple(params))
    conn.commit()
    return {"success": True, "updated": cur.rowcount}

def delete_resume_analysis(analysis_id: int):
    cur.execute("DELETE FROM resume_analysis WHERE analysis_id = ?", (analysis_id,))
    conn.commit()
    return {"success": True, "deleted": cur.rowcount}

# -----------------------------
# CRUD: Job Recommendations
# -----------------------------
def save_job_recommendation(
    user_id: int,
    job_title: str,
    company_name: str,
    location: str,
    job_description: str,
    job_url: str,
    match_percentage: float,
    scraping_date: str = None,
    posted_date: str = None,
    salary_range: str = None,
    applicants_count: str = None,
    required_skills: list = None,
    job_type: str = None,
    matching_skills: list = None,
    missing_skills: list = None,
    analysis_summary: str = None,
    component_scores: dict = None
) -> dict:
    cur.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
    if cur.fetchone() is None:
        return {"success": False, "error": "User does not exist."}

    if job_url and not is_valid_url(job_url):
        return {"success": False, "error": "Invalid job URL."}

    if match_percentage is None:
        match_percentage = 0.0
    try:
        match_percentage = float(match_percentage)
    except ValueError:
        return {"success": False, "error": "match_percentage must be numeric."}

    scraping_date = scraping_date or iso_now()
    cur.execute(
        """
        INSERT INTO job_recommendations
        (user_id, job_title, company_name, location, job_description,
         job_url, match_percentage, scraping_date, posted_date, salary_range, 
         applicants_count, required_skills, job_type, matching_skills, 
         missing_skills, analysis_summary, component_scores, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            job_title,
            company_name,
            location,
            job_description,
            job_url,
            match_percentage,
            scraping_date,
            posted_date,
            salary_range,
            applicants_count,
            json.dumps(required_skills or []),
            job_type,
            json.dumps(matching_skills or []),
            json.dumps(missing_skills or []),
            json.dumps(analysis_summary or ""),
            json.dumps(component_scores or {}),
            "new"
        ),
    )
    conn.commit()
    return {"success": True, "job_id": cur.lastrowid}

def get_recommended_jobs(user_id: int, min_match: float = 0.0):
    cur.execute(
        """
        SELECT * FROM job_recommendations
        WHERE user_id = ? AND match_percentage >= ?
        ORDER BY match_percentage DESC
        """,
        (user_id, float(min_match)),
    )
    rows = cur.fetchall()
    results = []
    
    # Get column names dynamically to handle schema evolution safer
    col_names = [description[0] for description in cur.description]
    
    for r in rows:
        row_dict = dict(zip(col_names, r))
        
        # Parse JSON fields safely
        for json_field in ['required_skills', 'matching_skills', 'missing_skills', 'component_scores']:
            if row_dict.get(json_field):
                try:
                    row_dict[json_field] = json.loads(row_dict[json_field])
                except Exception:
                    row_dict[json_field] = [] if json_field != 'component_scores' else {}
            else:
                 row_dict[json_field] = [] if json_field != 'component_scores' else {}

        results.append(row_dict)
    return results

def update_job_status(job_id: int, status: str):
    cur.execute("UPDATE job_recommendations SET status = ? WHERE job_id = ?", (status, job_id))
    conn.commit()
    return {"success": True}

def delete_job_recommendation(job_id: int):
    cur.execute("DELETE FROM job_recommendations WHERE job_id = ?", (job_id,))
    conn.commit()
    return {"success": True, "deleted": cur.rowcount}

# -----------------------------
# Close connection helper
# -----------------------------
def close_db():
    conn.close()
