# backend/resume_parser.py
import os
import io
from datetime import datetime

import PyPDF2
import docx

from utils.database import (
    update_user,
    save_resume_analysis,
)


RESUME_DIR = os.path.join("data", "resumes")
os.makedirs(RESUME_DIR, exist_ok=True)


# -----------------------------
# Low-level text extraction
# -----------------------------
def _extract_from_pdf(file_bytes: bytes) -> str:
    reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
    text_parts = []
    for page in reader.pages:
        try:
            page_text = page.extract_text() or ""
        except Exception:
            page_text = ""
        text_parts.append(page_text)
    return "\n".join(text_parts).strip()


def _extract_from_docx(file_bytes: bytes) -> str:
    document = docx.Document(io.BytesIO(file_bytes))
    paragraphs = [p.text for p in document.paragraphs if p.text]
    return "\n".join(paragraphs).strip()


def extract_resume_text(file_bytes: bytes, filename: str) -> str:
    """
    Detects extension and extracts text accordingly.
    """
    _, ext = os.path.splitext(filename.lower())

    if ext == ".pdf":
        return _extract_from_pdf(file_bytes)
    elif ext == ".docx":
        return _extract_from_docx(file_bytes)
    else:
        raise ValueError("Unsupported file type. Please upload a PDF or DOCX.")


# -----------------------------
# High-level upload handler
# -----------------------------
def handle_resume_upload(user_id: int, uploaded_file) -> dict:
    """
    - Saves the uploaded file under data/resumes/
    - Extracts text
    - Updates users.resume_file_path
    - Creates a basic resume_analysis entry

    uploaded_file is a Streamlit UploadedFile object.
    """
    original_name = uploaded_file.name
    _, ext = os.path.splitext(original_name.lower())

    if ext not in [".pdf", ".docx"]:
        return {"success": False, "error": "Only PDF and DOCX files are supported."}

    # Build a unique filename
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    new_filename = f"user_{user_id}_{timestamp}{ext}"
    file_path = os.path.join(RESUME_DIR, new_filename)

    # Save file to disk
    file_bytes = uploaded_file.getvalue()
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    # Extract text
    try:
        extracted_text = extract_resume_text(file_bytes, original_name)
    except Exception as e:
        return {"success": False, "error": f"Failed to read resume: {e}"}

    # Update user with resume path
    update_user(user_id, resume_file_path=file_path)

    # Save basic analysis record (for now only extracted text)
    analysis_result = save_resume_analysis(
        user_id=user_id,
        extracted_text=extracted_text,
        analysis_scores={},
        strengths=[],
        weaknesses=[],
        identified_skills=[],
        recommended_skills=[],
    )

    return {
        "success": True,
        "file_path": file_path,
        "extracted_text": extracted_text,
        "analysis_id": analysis_result.get("analysis_id"),
    }
