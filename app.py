# app.py
import streamlit as st

from frontend.login import render_login
from frontend.registration import render_registration
from frontend.dashboard import render_dashboard
from frontend.upload_resume import render_upload_resume
from frontend.job_recommendations import render_job_recommendations
from frontend.profile import render_profile
from frontend.analysis import render_analysis
from frontend.skills_gap import render_skills_gap
from frontend.job_preferences import render_job_preferences
from backend.auth import is_logged_in, get_current_user


def inject_custom_css():
    st.markdown(
        """
        <style>
        /* Main background */
        [data-testid="stAppViewContainer"] {
            background: radial-gradient(circle at top left, #1d4ed8 0, #020617 40%, #020617 100%);
            color: #f9fafb;
        }

        /* Push content down so top part is fully visible */
        .block-container {
            padding-top: 4rem;          /* was 1.5rem */
            padding-bottom: 3rem;
            max-width: 1100px;
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #020617 0%, #111827 60%, #020617 100%);
            color: #e5e7eb;
        }

        /* Buttons */
        .stButton>button {
            border-radius: 999px;
            padding: 0.5rem 1.2rem;
            border: none;
            font-weight: 600;
            box-shadow: 0 10px 25px rgba(15,23,42,0.55);
            transition: transform 0.08s ease-out, box-shadow 0.08s ease-out, background 0.1s;
        }
        .stButton>button:hover {
            transform: translateY(-1px);
            box-shadow: 0 16px 30px rgba(15,23,42,0.7);
        }

        /* Glass cards */
        .glass-card {
            background: rgba(15,23,42,0.92);
            border-radius: 1.7rem;
            padding: 1.8rem 2.0rem;
            border: 1px solid rgba(148,163,184,0.45);
            box-shadow: 0 20px 45px rg
            ba(15,23,42,0.95);
        }

        h1, h2, h3 {
            font-weight: 700 !important;
        }

        footer {visibility: hidden;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def main():
    st.set_page_config(
        page_title="Smart Resume Assistant",
        page_icon="🧠",
        layout="wide",
    )

    inject_custom_css()

    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "Dashboard" if is_logged_in() else "Login"

    pages = {
        "Login": render_login,
        "Register": render_registration,
        "Dashboard": render_dashboard,
        "My Profile": render_profile,
        "Upload Resume": render_upload_resume,
        "Resume Analysis": render_analysis,
        "Skills Gap": render_skills_gap,    # Now mapping to the real Skills Gap page
        "Resume Scoring": render_analysis,  # Mapping to Analysis for now
        "Job Preferences": render_job_preferences,
        "Job Recommendations": render_job_recommendations,
        "Suggestions": render_analysis, # Mapping to Analysis/Suggestions view
    }

    # === SIDEBAR NAVIGATION ===
    st.sidebar.title("🧠 Smart Resume Assistant")

    if is_logged_in():
        # When logged in: only show actual app pages
        page_names = [
            "Dashboard", 
            "My Profile", 
            "Upload Resume", 
            "Resume Analysis", 
            "Skills Gap", 
            "Resume Scoring", 
            "Job Preferences", 
            "Job Recommendations", 
            "Suggestions"
        ]
    else:
        # When logged out: only auth pages
        page_names = ["Login", "Register"]

    # If current_page is not allowed in this state, reset it
    if st.session_state["current_page"] not in pages:
        st.session_state["current_page"] = "Login"

    if is_logged_in() and st.session_state["current_page"] not in page_names:
        # If the current page isn't in the new list but we are logged in, default to Dashboard
        # This handles the case where a user was on "AI Analysis" which is now "Resume Analysis"
        st.session_state["current_page"] = "Dashboard"
        
    if (not is_logged_in()) and st.session_state["current_page"] not in page_names:
        st.session_state["current_page"] = "Login"

    current = st.sidebar.radio(
        "Navigation", # Changed label to match screenshot "Navigation" style (though Streamlit radio label is usually above)
        page_names,
        index=page_names.index(st.session_state["current_page"])
        if st.session_state["current_page"] in page_names
        else 0,
    )

    st.session_state["current_page"] = current

    # === TOP RIGHT PROFILE BUTTON REMOVED (Moved to Sidebar) ===
    if is_logged_in():
        user = get_current_user()
        # Optional: small greeting
        st.sidebar.markdown(f"---")
        st.sidebar.markdown(f"👋 Logged in as **{user['name']}**")

    # === RENDER CURRENT PAGE ===
    pages[st.session_state["current_page"]]()


if __name__ == "__main__":
    main()
