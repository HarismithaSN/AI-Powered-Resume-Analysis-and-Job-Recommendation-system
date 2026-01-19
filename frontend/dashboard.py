# frontend/dashboard.py
import streamlit as st

from backend.auth import require_login
from utils.database import (
    get_resume_analysis_by_user,
    get_recommended_jobs,
)


def render_dashboard():
    user = require_login()
    
    # Check status
    resume_uploaded = bool(user.get("resume_file_path"))
    analyses = get_resume_analysis_by_user(user["user_id"])
    jobs = get_recommended_jobs(user["user_id"], min_match=0.0)
    
    last_analysis_status = "Completed" if analyses else "Pending"
    job_match_count = len(jobs)
    
    # --- Header ---
    st.markdown(f"# Welcome, {user['name']} 👋")
    
    # --- Quick Stats ---
    st.markdown("### 📊 Quick Stats")
    
    col1, col2, col3 = st.columns(3)
    
    # CSS for the blue stats cards
    card_style = """
        background: linear-gradient(180deg, #0056b3 0%, #004494 100%);
        border-radius: 12px;
        padding: 20px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    """
    
    with col1:
        st.markdown(
            f"""
            <div style="{card_style}">
                <div style="font-size: 1rem; opacity: 0.9; margin-bottom: 5px;">📄 Resume Uploaded</div>
                <div style="font-size: 1.5rem; font-weight: bold;">{'Yes' if resume_uploaded else 'No'}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    with col2:
        st.markdown(
            f"""
            <div style="{card_style}">
                <div style="font-size: 1rem; opacity: 0.9; margin-bottom: 5px;">🔴 Last Analysis</div>
                <div style="font-size: 1.5rem; font-weight: bold;">{last_analysis_status}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            f"""
            <div style="{card_style}">
                <div style="font-size: 1rem; opacity: 0.9; margin-bottom: 5px;">💼 Job Matches</div>
                <div style="font-size: 1.5rem; font-weight: bold;">{job_match_count}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("---")

    # --- Recent Activity ---
    st.markdown("### 🕒 Recent Activity")
    
    # Simulate activity items based on state
    activity_html = """<div style="background-color: #f0f9ff; padding: 20px; border-radius: 10px; color: #1e293b;">"""
    
    # Item 1: Resume Uploaded
    if resume_uploaded:
        activity_html += """
<div style="margin-bottom: 10px; display: flex; align-items: center;">
    <span style="font-weight: bold; margin-right: 10px;">•</span> ✔ Resume uploaded
</div>
"""
    else:
        activity_html += """
<div style="margin-bottom: 10px; display: flex; align-items: center; color: #94a3b8;">
    <span style="font-weight: bold; margin-right: 10px;">•</span> ⏳ Resume not yet uploaded
</div>
"""

    # Item 2: Analysis Viewed
    if analyses:
        activity_html += """
<div style="margin-bottom: 10px; display: flex; align-items: center;">
    <span style="font-weight: bold; margin-right: 10px;">•</span> 📊 Analysis viewed
</div>
"""
    else:
        activity_html += """
<div style="margin-bottom: 10px; display: flex; align-items: center; color: #94a3b8;">
    <span style="font-weight: bold; margin-right: 10px;">•</span> ⏳ Analysis pending
</div>
"""

    # Item 3: Job Suggestions
    if jobs:
        activity_html += """
<div style="display: flex; align-items: center;">
    <span style="font-weight: bold; margin-right: 10px;">•</span> 💼 Job suggestions opened
</div>
"""
    else:
        activity_html += """
<div style="display: flex; align-items: center; color: #94a3b8;">
    <span style="font-weight: bold; margin-right: 10px;">•</span> ⏳ No jobs found yet
</div>
"""
        
    activity_html += "</div>"
    
    st.markdown(activity_html, unsafe_allow_html=True)
    
    st.markdown("---")

    # --- Quick Actions ---
    st.markdown("### 🚀 Quick Actions")
    
    qa_col1, qa_col2, qa_col3 = st.columns(3)
    
    # Helper to create buttons that navigate
    def action_button(col, title, subtitle, target_page):
        with col:
            # We use a button that updates session state to navigate
            # To make it look like the card in the screenshot, we might just use a button
            # But standard streamlit buttons are simple. 
            # We will use st.button and if clicked, change state.
            
            # Use a container for visual grouping (optional, streamlit columns are already containers)
            if st.button(f"{title}\n\n{subtitle}", use_container_width=True, key=title):
                st.session_state["current_page"] = target_page
                st.rerun()

    action_button(qa_col1, "📤 Upload Resume", "Start your analysis", "Upload Resume")
    action_button(qa_col2, "📊 Resume Analysis", "View strengths & weaknesses", "Resume Analysis")
    action_button(qa_col3, "✅ Resume Score", "Check ATS score", "Resume Scoring")

