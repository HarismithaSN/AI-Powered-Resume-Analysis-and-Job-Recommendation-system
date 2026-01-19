# frontend/profile.py
import streamlit as st

from backend.auth import require_login, logout
from utils.database import update_user


def _profile_completion(user) -> float:
    """Simple completion % based on how many fields are filled."""
    fields = [
        user.get("name"),
        user.get("college_name"),
        user.get("course"),
        user.get("graduation_year"),
        user.get("resume_file_path"),
    ]
    filled = sum(1 for v in fields if v not in (None, "", " "))
    return filled / len(fields)

def render_profile():
    user = require_login()

    # --- Back Button to Dashboard ---
    back_col1, back_col2 = st.columns([8, 2])
    with back_col2:
        if st.button("← Go Back"):
            st.session_state["current_page"] = "Dashboard"
            st.rerun()

    completion = _profile_completion(user)
    completion_percent = int(completion * 100)

    st.markdown(
        f"""
        <div class="glass-card">
          <div style="display:flex; justify-content:space-between; align-items:center; gap:1.5rem;">
            <div style="display:flex; align-items:center; gap:1rem;">
              <div style="
                  width:70px; height:70px; border-radius:50%;
                  background:linear-gradient(135deg,#4f46e5,#22c55e);
                  display:flex; align-items:center; justify-content:center;
                  font-size:2.0rem; font-weight:700; color:white;">
                  {user['name'][:1].upper()}
              </div>
              <div>
                <h2 style="margin-bottom:0.25rem; font-size:1.6rem;">My Profile</h2>
                <p style="margin:0; color:#cbd5f5; font-size:0.95rem;">
                  Update your personal and academic details here.
                </p>
              </div>
            </div>
            <div style="text-align:right;">
              <span style="
                  font-size:0.8rem;
                  text-transform:uppercase;
                  letter-spacing:0.08em;
                  color:#9ca3af;">Profile completeness</span>
              <div style="margin-top:0.3rem; font-size:1.1rem; font-weight:600;">
                {completion_percent}%
              </div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Progress bar under card (interactive feel)
    st.progress(completion)

    st.write("")

    # ---------- Editable fields ----------
    col1, col2 = st.columns(2)

    with col1:
        new_name = st.text_input("Full Name", value=user["name"], key="profile_name")
        college = st.text_input(
            "College Name",
            value=user.get("college_name") or "",
            key="profile_college",
            placeholder="e.g., Dayananda Sagar College of Engineering",
        )
    with col2:
        st.text_input("Email (cannot be changed)", value=user["email"], disabled=True)
        course = st.text_input(
            "Course / Program",
            value=user.get("course") or "",
            key="profile_course",
            placeholder="e.g., MCA",
        )
        grad_year = st.text_input(
            "Graduation Year",
            value=user.get("graduation_year") or "",
            key="profile_grad_year",
            placeholder="e.g., 2026",
        )
    
    col3, col4 = st.columns(2)
    with col3:
        current_role = st.text_input(
            "Current Role",
            value=user.get("current_role") or "",
            key="profile_role",
            placeholder="e.g., Student / Software Engineer"
        )
    with col4:
        exp_years = st.text_input(
            "Years of Experience",
            value=user.get("experience_years") or "",
            key="profile_exp",
            placeholder="e.g., 2 Years"
        )

    col_btn1, col_btn2 = st.columns([1.2, 3])
    with col_btn1:
        if st.button("💾 Save profile"):
            res = update_user(
                user["user_id"],
                name=new_name.strip(),
                college_name=college.strip() or None,
                course=course.strip() or None,
                graduation_year=grad_year.strip() or None,
                current_role=current_role.strip() or None,
                experience_years=exp_years.strip() or None,
            )
            if res["success"]:
                user["name"] = new_name.strip()
                user["college_name"] = college.strip() or None
                user["course"] = course.strip() or None
                user["graduation_year"] = grad_year.strip() or None
                user["current_role"] = current_role.strip() or None
                user["experience_years"] = exp_years.strip() or None
                st.session_state["user"] = user
                st.success("Profile updated successfully!")
            else:
                st.error(res.get("error", "Failed to update profile."))
    with col_btn2:
        st.caption(f"Member since {user['registration_date']}")

    st.write("")
    st.markdown("---")

    # ---------- Extra interactive bit: quick summary ----------
    st.subheader("Summary")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Name:** " + (user.get("name") or "—"))
        st.markdown("**College:** " + (user.get("college_name") or "Not set"))
        st.markdown("**Course:** " + (user.get("course") or "Not set"))
    with col_b:
        st.markdown("**Graduation year:** " + (user.get("graduation_year") or "Not set"))
        st.markdown(
            "**Resume linked:** "
            + ("Yes ✅" if user.get("resume_file_path") else "No ❌")
        )

    st.markdown("---")
    st.markdown("### Session")

    logout_col1, logout_col2 = st.columns([1, 3])
    with logout_col1:
        if st.button("🚪 Logout"):
            logout()
            st.session_state["current_page"] = "Login"
            st.rerun()
    with logout_col2:
        st.write("Log out of your account and return to the login screen.")
