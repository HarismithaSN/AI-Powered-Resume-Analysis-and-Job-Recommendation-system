# frontend/login.py
import streamlit as st

from backend.auth import login_user, set_current_user


def render_login():
    st.title("Login")

    if "user" in st.session_state and st.session_state["user"] is not None:
        st.info(f"You are already logged in as {st.session_state['user']['email']}.")
        return

    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

    if submitted:
        result = login_user(email, password)
        if not result["success"]:
            st.error(result["error"])
        else:
            set_current_user(result["user"])
            st.success("Login successful!")
            # Navigate to dashboard in main app
            st.session_state["current_page"] = "Dashboard"
            st.rerun()

