# app.py
import streamlit as st

from frontend.login import render_login
from frontend.registration import render_registration
from frontend.dashboard import render_dashboard
from frontend.upload_resume import render_upload_resume
from frontend.profile import render_profile
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
            box-shadow: 0 20px 45px rgba(15,23,42,0.95);
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
        "Upload Resume": render_upload_resume,
        "Profile": render_profile,
    }

    # === SIDEBAR NAVIGATION ===
    st.sidebar.title("🧠 Smart Resume Assistant")

    if is_logged_in():
        # When logged in: only show actual app pages
        page_names = ["Dashboard", "Upload Resume"]
    else:
        # When logged out: only auth pages
        page_names = ["Login", "Register"]

    # If current_page is not allowed in this state, reset it
    if st.session_state["current_page"] not in pages:
        st.session_state["current_page"] = "Login"

    if is_logged_in() and st.session_state["current_page"] not in page_names + ["Profile"]:
        st.session_state["current_page"] = "Dashboard"
    if (not is_logged_in()) and st.session_state["current_page"] not in page_names:
        st.session_state["current_page"] = "Login"

    current = st.sidebar.radio(
        "Go to",
        page_names,
        index=page_names.index(st.session_state["current_page"])
        if st.session_state["current_page"] in page_names
        else 0,
    )

    # Only change via sidebar if not currently on Profile
    if st.session_state.get("current_page") != "Profile":
        st.session_state["current_page"] = current

    # === TOP RIGHT PROFILE BUTTON (only when logged in) ===
    if is_logged_in():
        user = get_current_user()
        top_col1, top_col2 = st.columns([6, 2])
        with top_col1:
            # Optional: small greeting on each page
            st.markdown(f"###### 👋 Logged in as **{user['name']}**")
        with top_col2:
            if st.button("👤 Profile", key="profile_top_button"):
                st.session_state["current_page"] = "Profile"
                st.rerun()

    # === RENDER CURRENT PAGE ===
    pages[st.session_state["current_page"]]()


if __name__ == "__main__":
    main()
