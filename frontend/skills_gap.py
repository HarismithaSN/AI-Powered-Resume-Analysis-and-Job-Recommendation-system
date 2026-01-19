# frontend/skills_gap.py
import streamlit as st
import plotly.graph_objects as go
from backend.auth import require_login
from backend.llm_analyzer import LLMAnalyzer
from utils.database import get_resume_analysis_by_user

def render_skills_gap():
    user = require_login()
    
    st.markdown("# ⚔️ Advanced Skills Gap Analysis")
    st.markdown("Analyze your resume against a specific target role to identify missed opportunities and learning paths.")
    
    # --- Check for Resume ---
    # We can check if file path exists or if there is past analysis
    resume_path = user.get("resume_file_path")
    analyses = get_resume_analysis_by_user(user["user_id"])
    
    # If no resume analysis found, we might need text from file (not implemented fully to read raw file here yet)
    # So we prefer using the latest analysis text if available
    if not analyses:
        st.warning("Please upload a resume and run an initial analysis first.")
        if st.button("Go to Upload"):
            st.session_state["current_page"] = "Upload Resume"
            st.rerun()
        return

    latest_analysis = analyses[0]
    resume_text = latest_analysis["extracted_resume_text"]
    
    if not resume_text:
        st.error("Could not retrieve resume text. Please re-upload your resume.")
        return

    # --- Controls ---
    with st.container():
        st.markdown("### Target Role Configuration")
        col1, col2 = st.columns(2)
        with col1:
            target_role = st.selectbox(
                "Target Job Role",
                [
                    "Software Engineer",
                    "Data Scientist", 
                    "Product Manager",
                    "Frontend Developer",
                    "Backend Developer",
                    "Full Stack Developer",
                    "DevOps Engineer",
                    "Business Analyst",
                    "Other"
                ]
            )
            if target_role == "Other":
                target_role = st.text_input("Enter Role Name")
                
        with col2:
            experience_level = st.selectbox(
                "Experience Level",
                ["Fresher (0-1 years)", "Junior (1-3 years)", "Mid-Level (3-5 years)", "Senior (5+ years)", "Lead/Principal"]
            )
            
        analyze_btn = st.button("Analyze Skills Gap", type="primary", use_container_width=True)
        
        # demo mode toggle
        use_demo = st.sidebar.checkbox("Enable Demo Mode", value=False, help="Use mock data for instant results.")

    # --- State Management for Result ---
    if "skills_gap_result" not in st.session_state:
        st.session_state["skills_gap_result"] = None
        
    if analyze_btn:
        if not target_role:
             st.error("Please specify a target role.")
        else:
            with st.spinner("Consulting AI expert..."):
                analyzer = LLMAnalyzer()
                if use_demo:
                    analyzer.mock_mode = True
                    
                result = analyzer.analyze_skills_gap(resume_text, target_role, experience_level)
                
                if "error" in result:
                    st.error(f"Analysis failed: {result['error']}")
                else:
                    st.session_state["skills_gap_result"] = result

    # --- Display Results ---
    result = st.session_state["skills_gap_result"]
    if result:
        st.markdown("---")
        
        # Summary
        st.markdown(f"### Analysis for **{target_role}**")
        
        # Match Score
        # Match Score Gauge
        score = result.get("match_score", 0)
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = score,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Role Match Score"},
            gauge = {
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': "#4ade80" if score >= 80 else "#fcd34d" if score >= 50 else "#fca5a5"},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 50], 'color': '#fca5a5'},
                    {'range': [50, 80], 'color': '#fcd34d'},
                    {'range': [80, 100], 'color': '#dcfce7'}],
                'threshold': {
                    'line': {'color': "black", 'width': 4},
                    'thickness': 0.75,
                    'value': score
                }
            }
        ))
        fig.update_layout(height=300, margin=dict(l=20, r=20, t=30, b=20), paper_bgcolor="rgba(0,0,0,0)", font={'color': "white"})
        st.plotly_chart(fig, use_container_width=True)
        st.info(result.get('summary', ''))

        # Matched vs Missing (Must Have)
        st.markdown("#### 🔑 Critical Skills (Must Have)")
        c1, c2 = st.columns(2)
        must_have = result.get("must_have", {})
        
        with c1:
            st.markdown("**✅ Matched**")
            if must_have.get("matched"):
                for s in must_have["matched"]:
                    st.success(s)
            else:
                st.caption("No critical matches found.")
                
        with c2:
            st.markdown("**🚫 Missing**")
            if must_have.get("missing"):
                for s in must_have["missing"]:
                    st.error(s)
            else:
                st.caption("No critical gaps!")

        st.markdown("---")
        
        # Nice to Have (Advanced)
        st.markdown("#### 🌟 Bonus Skills (Nice to Have)")
        nc1, nc2 = st.columns(2)
        nice_have = result.get("nice_to_have", {})
        
        with nc1:
            st.markdown("**✅ Matched**")
            if nice_have.get("matched"):
                for s in nice_have["matched"]:
                    st.info(s)
            else:
                st.caption("No bonus matches.")
        
        with nc2:
            st.markdown("**🚫 To Learn**")
            if nice_have.get("missing"):
                for s in nice_have["missing"]:
                    st.warning(s)
            else:
                st.caption("All bonus skills covered.")

        st.markdown("---")

        # Recommendations / Learning Path (Page 9 Style)
        st.markdown("### 🎓 Learning Recommendations")
        recs = result.get("recommendations", [])
        
        if not recs:
            st.info("No specific recommendations generated.")
        else:
            for i, rec in enumerate(recs):
                st.markdown(f"""
                <div style="background:rgba(255,255,255,0.05); padding:15px; border-radius:10px; margin-bottom:10px; border-left: 4px solid #3b82f6;">
                    <h4 style="margin:0 0 5px 0;">{i+1}. {rec.get('skill', 'Skill')}</h4>
                    <p style="margin:0 0 8px 0; font-size:0.95rem; color:#cbd5e1;"><em>{rec.get('why_important', '')}</em></p>
                    <div style="font-size:0.9rem;">
                        <strong>📚 Resources:</strong> 
                        {' | '.join([f'<a href="https://www.google.com/search?q={r.replace(" ", "+")}" target="_blank" style="color:#60a5fa; text-decoration:none;">{r}</a>' for r in rec.get('learning_resources', [])])}
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")
        
        # Page 6: Data Processing View
        with st.expander("🔍 View Raw Analysis Data (Page 6 Mode)"):
            st.json(result)

