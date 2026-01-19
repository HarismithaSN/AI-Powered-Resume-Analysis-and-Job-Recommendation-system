# frontend/upload_resume.py
import streamlit as st

from backend.auth import require_login
from backend.resume_parser import handle_resume_upload, delete_resume_for_user


def render_upload_resume():
    user = require_login()

    st.markdown(
        """
        <div class="glass-card">
          <h2 style="margin-bottom:0.25rem;">📄 Upload Resume</h2>
          <p style="margin:0; color:#cbd5f5; font-size:0.9rem;">
            Upload your latest resume in PDF or DOCX format. You can re-upload or delete it anytime.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")

    # Show current resume status
    if user.get("resume_file_path"):
        st.success(f"Current resume on file: `{user['resume_file_path']}`")
        col_del1, col_del2 = st.columns([1, 3])
        with col_del1:
            if st.button("🗑 Delete current resume"):
                result = delete_resume_for_user(
                    user_id=user["user_id"],
                    resume_path=user.get("resume_file_path"),
                )
                if result["success"]:
                    st.session_state["user"]["resume_file_path"] = None
                    # Clear analysis state
                    if "resume_text" in st.session_state:
                        del st.session_state["resume_text"]
                    if "uploaded_filename" in st.session_state:
                        del st.session_state["uploaded_filename"]
                    
                    st.success("Resume deleted successfully.")
                    st.rerun()
                else:
                    st.error(result.get("error", "Failed to delete resume."))
        with col_del2:
            st.write("")

        st.markdown("---")

    st.write("Upload a new resume (PDF/DOCX, max ~5 MB).")

    uploaded_file = st.file_uploader("Choose a file", type=["pdf", "docx"])
    if uploaded_file is not None:
        st.write(f"Selected file: `{uploaded_file.name}`")
        st.write(f"Size: {uploaded_file.size / 1024:.2f} KB")

    if st.button("⬆ Upload & Analyze", disabled=uploaded_file is None):
        if uploaded_file is None:
            st.error("Please select a file first.")
            return

        with st.spinner("Uploading and analyzing your resume..."):
            result = handle_resume_upload(user_id=user["user_id"], uploaded_file=uploaded_file)
            
            # Simulation of processing time for effect
            import time
            time.sleep(1)

        if not result["success"]:
            st.error(result["error"])
        else:
            # Update session user resume_file_path
            st.session_state["user"]["resume_file_path"] = result["file_path"]
            
            # Save text for the Analysis page
            st.session_state["resume_text"] = result["extracted_text"]
            st.session_state["uploaded_filename"] = uploaded_file.name

            st.success("Resume processed! Redirecting to analysis...")
            time.sleep(1)
            st.session_state["current_page"] = "AI Analysis"
            st.rerun()
