# frontend/upload_resume.py
import streamlit as st

from backend.auth import require_login
from backend.resume_parser import handle_resume_upload


def render_upload_resume():
    user = require_login()

    st.title("Upload Resume")

    st.write("Upload your resume in **PDF** or **DOCX** format (max ~5 MB).")

    uploaded_file = st.file_uploader("Choose a file", type=["pdf", "docx"])
    if uploaded_file is not None:
        st.write(f"Selected file: `{uploaded_file.name}`")
        st.write(f"Size: {uploaded_file.size / 1024:.2f} KB")

    if st.button("Upload & Analyze", disabled=uploaded_file is None):
        if uploaded_file is None:
            st.error("Please select a file first.")
            return

        with st.spinner("Uploading and analyzing your resume..."):
            result = handle_resume_upload(user_id=user["user_id"], uploaded_file=uploaded_file)

        if not result["success"]:
            st.error(result["error"])
        else:
            st.success("Resume uploaded and basic analysis saved!")
            if result.get("extracted_text"):
                with st.expander("Show extracted resume text"):
                    st.text(result["extracted_text"])

            # Update session user resume_file_path so dashboard shows correct status
            st.session_state["user"]["resume_file_path"] = result["file_path"]
