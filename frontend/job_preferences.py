import streamlit as st
import time

def render_job_preferences():
    st.title("🎯 Job Search Preferences")
    st.markdown("Customize your job search for better recommendations")
    st.markdown("---")

    # Custom CSS for form styling
    st.markdown("""
    <style>
    .stTextInput > label, .stSelectbox > label, .stMultiSelect > label, .stNumberInput > label {
        font-weight: 600;
        color: #e5e7eb;
    }
    .stRadio > label {
        font-weight: 600;
        color: #e5e7eb;
    }
    </style>
    """, unsafe_allow_html=True)

    with st.container():
        st.subheader("🔧 Basic Preferences")
        
        # Desired Job Title
        job_title = st.text_input("Desired Job Title", placeholder="e.g. Python Developer")
        
        # Preferred Locations using Tags (multiselect)
        locations = st.multiselect(
            "Preferred Locations",
            ["Hyderabad", "Bangalore", "Pune", "Mumbai", "Chennai", "Delhi", "Remote", "USA", "UK"],
            default=["Bangalore"]
        )
        
        # Remote Preference
        remote_pref = st.radio(
            "Remote Preference",
            ["Any", "Only Remote", "Hybrid", "On-site"],
            index=0,
            horizontal=True
        )
        
        col1, col2 = st.columns(2)
        with col1:
             # Experience Level
             experience = st.selectbox(
                 "Experience Level",
                 ["Entry Level", "Mid Level", "Senior Level", "Executive", "Internship"]
             )
        
        with col2:
            # Job Type
            job_type = st.selectbox(
                "Job Type",
                ["Full-time", "Part-time", "Contract", "Freelance", "Internship"]
            )

        # Minimum Salary
        salary = st.number_input("Minimum Salary Expectation (optional)", min_value=0, step=1000, help="Annual salary in USD or local currency")

        # Industries
        industries = st.multiselect(
            "Industries of Interest",
            ["Tech", "Finance", "Healthcare", "Education", "Consulting", "Retail", "Manufacturing"],
            default=["Tech"]
        )

        # Company Size
        company_size = st.selectbox(
            "Company Size Preference",
            ["Any", "Startup (1-50)", "Small (51-200)", "Mid-sized (201-1000)", "Large (1000+)"]
        )
        
        st.markdown("---")
        
        # Advanced Preferences Expandable (as seen in screenshot bottom)
        with st.expander("⚙️ Advanced Preferences"):
            st.write("Additional filters configuration could go here.")
            st.checkbox("Exclude staffing agencies")
            st.checkbox("Only companies with high ratings")

        st.markdown("<br>", unsafe_allow_html=True)

        # Buttons
        b_col1, b_col2 = st.columns([1, 4])
        with b_col1:
            if st.button("💾 Save Preferences"):
                # Save to session state or DB
                st.session_state["job_prefs"] = {
                    "title": job_title,
                    "locations": locations,
                    "remote": remote_pref,
                    "experience": experience,
                    "job_type": job_type,
                    "salary": salary,
                    "industries": industries,
                    "company_size": company_size
                }
                st.success("Preferences Saved!")
        
        with b_col2:
            if st.button("🔎 Find Jobs Now"):
                st.session_state["current_page"] = "Job Recommendations"
                # Pass query parameters if needed
                st.session_state["search_query_seed"] = job_title
                st.rerun()
