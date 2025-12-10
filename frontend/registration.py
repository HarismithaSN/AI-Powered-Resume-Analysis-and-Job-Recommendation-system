# frontend/registration.py
import re
import streamlit as st

from backend.auth import register_user


PASSWORD_REGEX = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,}$"
)


def render_registration():
    st.title("Create an Account")

    with st.form("registration_form"):
        name = st.text_input("Full Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")

        submitted = st.form_submit_button("Register")

    if submitted:
        # Additional password strength check (DB already enforces length >= 8)
        if not PASSWORD_REGEX.match(password or ""):
            st.error(
                "Password must be at least 8 characters and include uppercase, "
                "lowercase, number, and special character."
            )
            return

        result = register_user(name, email, password, confirm_password)
        if not result["success"]:
            st.error(result["error"])
        else:
            st.success("Registration successful! You can now log in.")
            # After successful registration, move to login page
            st.session_state["current_page"] = "Login"
            st.rerun()

