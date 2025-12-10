# backend/auth.py
from typing import Dict, Any
import streamlit as st

from utils.database import (
    create_user,
    get_user_with_password,
    check_password,
)


def register_user(name: str, email: str, password: str, confirm_password: str) -> Dict[str, Any]:
    if not name or not name.strip():
        return {"success": False, "error": "Name is required."}
    if not email or not email.strip():
        return {"success": False, "error": "Email is required."}
    if password != confirm_password:
        return {"success": False, "error": "Passwords do not match."}

    # For now we only pass basic info; college is edited in Profile tab
    return create_user(name=name.strip(), email=email.strip(), plain_password=password)


def login_user(email: str, password: str) -> Dict[str, Any]:
    if not email or not password:
        return {"success": False, "error": "Email and password are required."}

    user_row = get_user_with_password(email)
    if user_row is None:
        return {"success": False, "error": "User not found."}

    if not check_password(password, user_row["hashed_password"]):
        return {"success": False, "error": "Incorrect password."}

    user = {
        "user_id": user_row["user_id"],
        "name": user_row["name"],
        "email": user_row["email"],
        "registration_date": user_row["registration_date"],
        "resume_file_path": user_row["resume_file_path"],
        "college_name": user_row.get("college_name"),
        "course": user_row.get("course"),
        "graduation_year": user_row.get("graduation_year"),
    }
    return {"success": True, "user": user}


# Session helpers
def set_current_user(user: Dict[str, Any]) -> None:
    st.session_state["user"] = user

def get_current_user() -> Dict[str, Any] | None:
    return st.session_state.get("user")

def is_logged_in() -> bool:
    return "user" in st.session_state and st.session_state["user"] is not None

def require_login() -> Dict[str, Any]:
    user = get_current_user()
    if not user:
        st.warning("You need to log in to access this page.")
        st.stop()
    return user

def logout() -> None:
    if "user" in st.session_state:
        del st.session_state["user"]
