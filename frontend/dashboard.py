# frontend/dashboard.py
import streamlit as st

from backend.auth import require_login
from utils.database import (
    get_resume_analysis_by_user,
    get_recommended_jobs,
)


def render_dashboard():
    user = require_login()

    # Header card
    st.markdown(
        f"""
        <div class="glass-card">
          <div style="display:flex; align-items:center; gap:1rem;">
            <div style="
                width:56px; height:56px; border-radius:50%;
                background:linear-gradient(135deg,#4f46e5,#22c55e);
                display:flex; align-items:center; justify-content:center;
                font-size:1.5rem; font-weight:700; color:white;">
                {user['name'][:1].upper()}
            </div>
            <div>
              <h2 style="margin-bottom:0.1rem;">Welcome back, {user['name']} 👋</h2>
              <p style="margin:0; color:#cbd5f5; font-size:0.9rem;">
                Check your resume status and job matches.
              </p>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")

    analyses = get_resume_analysis_by_user(user["user_id"])
    jobs = get_recommended_jobs(user["user_id"], min_match=0.0)

    resume_uploaded = bool(user.get("resume_file_path"))
    last_analysis = analyses[0]["analysis_timestamp"] if analyses else "No analysis yet"
    num_jobs = len(jobs)

    tab_overview, tab_resume, tab_jobs = st.tabs(
        ["📊 Overview", "📄 Resume & Analysis", "💼 Jobs"]
    )

    # ---------- OVERVIEW ----------
    with tab_overview:
        st.subheader("Quick stats")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Resume Uploaded", "Yes" if resume_uploaded else "No")
        with c2:
            st.metric("Last Analysis", last_analysis)
        with c3:
            st.metric("Job Recommendations", num_jobs)

        st.write("")
        if analyses:
            st.info("Your latest resume has been analyzed. Check the Resume tab.")
        else:
            st.warning("No analysis yet. Upload your resume to get started!")

    # ---------- RESUME ----------
    with tab_resume:
        st.subheader("Resume & Analysis")

        if not resume_uploaded:
            st.warning("No resume uploaded yet. Use **Upload Resume** in the sidebar.")
        else:
            st.success("Resume uploaded ✔")
            st.write(f"Path: `{user['resume_file_path']}`")

        if analyses:
            st.markdown("### Latest extracted text")
            latest = analyses[0]
            with st.expander("Show extracted resume text"):
                st.text(latest["extracted_resume_text"])
        else:
            st.info("No analysis data available yet.")

    # ---------- JOBS ----------
    with tab_jobs:
        st.subheader("Job recommendations")

        if not jobs:
            st.info("No job recommendations yet. This will be added in later milestones.")
        else:
            min_match = st.slider("Minimum match %", 0, 100, 60)
            filtered = [j for j in jobs if j["match_percentage"] >= min_match]

            if not filtered:
                st.warning("No jobs above this match threshold.")
            else:
                for job in filtered:
                    st.markdown(
                        f"**{job['job_title']}** at **{job['company_name']}** "
                        f"({job['location']}) — `Match: {job['match_percentage']}%`"
                    )
                    st.write(job["job_description"][:250] + "...")
                    if job["job_url"]:
                        st.markdown(f"[View details]({job['job_url']})")
                    st.write("---")
