import streamlit as st
import plotly.graph_objects as go
from backend.llm_analyzer import LLMAnalyzer
from backend.auth import require_login
from utils.database import get_resume_analysis_by_user
import time
from datetime import datetime

def render_analysis():
    # Determine Context
    current_page = st.session_state.get("current_page", "Resume Analysis")
    user = require_login()
    
    # Mock Analysis Options
    default_index = 0
    if current_page == "Resume Scoring":
         st.title("🎯 Resume Scoring")
         default_index = 4 # Full Scoring
    else:
         st.title("🤖 AI Resume Analysis")
         
    st.markdown("---")

    # Custom CSS for Analysis Page
    st.markdown("""
    <style>
    div[data-testid="metric-container"] {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 10px;
        border-radius: 10px;
        transition: transform 0.2s;
    }
    div[data-testid="metric-container"]:hover {
        transform: scale(1.02);
        background-color: rgba(255, 255, 255, 0.1);
    }
    </style>
    """, unsafe_allow_html=True)
    
    if "resume_text" not in st.session_state:
        st.warning("⚠️ No resume found. Please upload one to begin analysis.")
        if st.button("📂 Upload Resume Now"):
            st.session_state["current_page"] = "Upload Resume"
            st.rerun()
        return

    st.write(f"**Analyzing resume for:** {st.session_state.get('uploaded_filename', 'Unknown File')}")
    
    # Validation
    if len(st.session_state["resume_text"]) < 50:
        st.error("⚠️ The resume text appears to be empty or unreadable. This often happens with scanned/image-based PDFs.")
        st.info("Please upload a standard text-based PDF or DOCX file.")
        if st.button("⬅ Go back to Upload"):
            st.session_state["current_page"] = "Upload Resume"
            st.rerun()
        return

    # Initialize LLM
    try:
        analyzer = LLMAnalyzer()
    except Exception:
        analyzer = None

    # Analysis Options
    analysis_options = ["Comprehensive Analysis", "General Review", "Strengths & Weaknesses", "Skills Gap", "Full Scoring"]
    
    # demo mode toggle
    use_demo = st.sidebar.checkbox("Enable Demo Mode", value=False, help="Use mock data for instant results (useful if local AI is slow).")
    
    analysis_type = st.selectbox("Choose Analysis Type", 
                                 analysis_options,
                                 index=default_index)

    if st.button("Run Analysis"):
        if not analyzer:
             st.error("AI Engine fatal error.")
        else:
             if use_demo:
                 analyzer.mock_mode = True
                 
             with st.spinner("Analyzing... (This may take a few seconds)"):
                if analyzer.mock_mode:
                    st.warning("⚠️ **Running in MOCK MODE**")
                    st.info("To get real AI analysis, get an API key from [Google AI Studio](https://aistudio.google.com/app/apikey) and put it in `.env`.")
                    time.sleep(1.5) # Simulate work
                    
                    # Run generic mock analysis
                    results = analyzer.analyze_resume_comprehensive(st.session_state["resume_text"])
                    st.session_state["analysis_results"] = results
                    st.success("Mock Analysis Complete!")
                    
                # Skip explicit connection check to prefer the retry logic in the actual analysis call
                # elif not analyzer.check_connection():
                #     st.error("Failed to connect to AI Service. Check your network or API Key.")
                else:
                    # Run the analysis
                    results = analyzer.analyze_resume_comprehensive(st.session_state["resume_text"])
                    if "error" in results:
                        st.error(f"Analysis Failed: {results['error']}")
                    else:
                        st.session_state["analysis_results"] = results
                        st.success("Analysis Complete!")

    st.markdown("---")
    
    # Custom CSS for Report View
    st.markdown("""
    <style>
    /* Report Container */
    .report-container {
        font-family: 'Inter', sans-serif;
        color: #e2e8f0;
    }
    
    /* Section Headers */
    .section-header {
        display: flex;
        align-items: center;
        font-size: 1.5rem;
        font-weight: 700;
        margin-top: 2rem;
        margin-bottom: 1rem;
        color: #f8fafc;
    }
    
    /* Candidate Card */
    .candidate-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(10px);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 2rem;
        color: #e2e8f0;
    }
    
    .candidate-info-row {
        margin-bottom: 0.5rem;
        font-size: 1rem;
    }
    
    .candidate-label {
        font-weight: 600;
        color: #94a3b8;
        width: 100px;
        display: inline-block;
    }
    
    /* Strength/Weakness Cards */
    .insight-card {
        padding: 1rem 1.5rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border-left: 5px solid;
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.05); /* Default border */
    }
    
    .strength-card {
        border-left-color: #22c55e;
        box-shadow: 0 4px 6px -1px rgba(34, 197, 94, 0.1);
    }
    
    .weakness-card {
        border-left-color: #ef4444;
        box-shadow: 0 4px 6px -1px rgba(239, 68, 68, 0.1);
    }
    
    .insight-title {
        font-weight: 600;
        font-size: 1.05rem;
        margin-bottom: 0.5rem;
        color: #f1f5f9;
        display: flex;
        align-items: center;
    }
    
    .insight-meta {
        display: flex;
        gap: 1.5rem;
        font-size: 0.85rem;
        color: #94a3b8;
        margin-top: 0.5rem;
    }

    .meta-item {
        display: flex;
        align-items: center;
        gap: 0.3rem;
    }

    /* Badge styling */
    .badge {
        padding: 0.2rem 0.6rem;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-critical { background: rgba(239, 68, 68, 0.2); color: #fca5a5; border: 1px solid rgba(239, 68, 68, 0.3); }
    .badge-moderate { background: rgba(249, 115, 22, 0.2); color: #fdba74; border: 1px solid rgba(249, 115, 22, 0.3); }
    .badge-minor { background: rgba(148, 163, 184, 0.2); color: #cbd5e1; border: 1px solid rgba(148, 163, 184, 0.3); }
    
    </style>
    """, unsafe_allow_html=True)
    
    # Check if we have results to display
    if "analysis_results" in st.session_state:
        results = st.session_state["analysis_results"]
        
        # Determine view mode: Score vs Report
        if current_page == "Resume Scoring":
            render_scoring_dashboard(results, user["user_id"])
        else:
            render_full_report(results)
    else:
        st.info("Select 'Comprehensive Analysis' and click 'Run Analysis' to see results.")

def render_scoring_dashboard(results, user_id):
    st.subheader("📊 Scoring Dashboard")
    score = results.get("score", 0)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Gauge Chart
        st.markdown("#### Current Score")
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = score,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "ATS Compatibility"},
            gauge = {
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': "#4ade80" if score >= 75 else "#fcd34d" if score >= 50 else "#fca5a5"}, 
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 50], 'color': '#fca5a5'}, # Red
                    {'range': [50, 75], 'color': '#fcd34d'}, # Yellow
                    {'range': [75, 100], 'color': '#dcfce7'}], # Green
                'threshold': {'line': {'color': "black", 'width': 4}, 'thickness': 0.75, 'value': score}
            }
        ))
        fig.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20), paper_bgcolor="rgba(0,0,0,0)", font={'color': "white"})
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Progress Timeline (Page 11 Requirement)
        st.markdown("#### Progress Over Time")
        history = get_resume_analysis_by_user(user_id)
        
        if len(history) < 2:
            st.info("Run more analyses to see your progress over time!")
        
        # Prepare data
        dates = []
        scores = []
        for h in reversed(history[:10]): # Last 10 points, chronological
            if h.get("analysis_scores"):
                try:
                    s_score = h["analysis_scores"].get("score", 0)
                    ts = h["analysis_timestamp"][:10] # YYYY-MM-DD
                    dates.append(ts)
                    scores.append(s_score)
                except:
                    pass
        
        if scores:
            fig_line = go.Figure(data=go.Scatter(x=dates, y=scores, mode='lines+markers', line=dict(color='#22c55e', width=3)))
            fig_line.update_layout(
                title=None,
                xaxis_title="Date",
                yaxis_title="Score",
                height=300,
                margin=dict(l=20, r=20, t=20, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font={'color': "white"},
                yaxis=dict(range=[0, 100])
            )
            st.plotly_chart(fig_line, use_container_width=True)

    st.markdown("---")
    
    # Section Breakdown
    if "section_analysis" in results:
        sections_data = results["section_analysis"]
        categories = ["Summary", "Experience", "Projects", "Skills", "Education"]
        r = [
            sections_data.get("summary_section", {}).get("score", 0),
            sections_data.get("experience_section", {}).get("score", 0),
            sections_data.get("projects_section", {}).get("score", 0),
            sections_data.get("skills_section", {}).get("score", 0),
            sections_data.get("education_section", {}).get("score", 0)
        ]
        
        fig_radar = go.Figure(go.Scatterpolar(r=r, theta=categories, fill='toself', name='Section Score'))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 10])), showlegend=False, 
                              height=350, margin=dict(l=40, r=40, t=20, b=20), 
                              paper_bgcolor="rgba(0,0,0,0)", font={'color': "white"}, title="Section Breakdown")
        st.plotly_chart(fig_radar, use_container_width=True)

def render_full_report(results):
    # Main Title
    st.markdown('<div class="section-header">📊 Full Resume Analysis Report</div>', unsafe_allow_html=True)
    
    # 1. Candidate Details
    name = results.get("candidate_name", "Not Found")
    email = results.get("candidate_email", "Not Found")
    phone = results.get("candidate_phone", "Not Found")
    
    st.markdown("### 👤 Candidate Details")
    st.markdown(f"""
    <div class="candidate-card">
        <div class="candidate-info-row"><span class="candidate-label">Name:</span> {name}</div>
        <div class="candidate-info-row"><span class="candidate-label">Email:</span> {email}</div>
        <div class="candidate-info-row"><span class="candidate-label">Phone:</span> {phone}</div>
    </div>
    """, unsafe_allow_html=True)

    # 1.5 Overall Score Gauge & Grid Analysis (New Requirement)
    st.markdown("### 🎯 Score & Breakdown")
    
    score = results.get("score", 0)
    
    # Top Row: Gauge + Summary
    gc1, gc2 = st.columns([1, 2])
    with gc1:
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = score,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Overall Match", 'font': {'size': 16, 'color': 'white'}},
            gauge = {
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': "#4ade80" if score >= 75 else "#fcd34d" if score >= 50 else "#fca5a5"}, 
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 50], 'color': '#fca5a5'},
                    {'range': [50, 75], 'color': '#fcd34d'},
                    {'range': [75, 100], 'color': '#dcfce7'}],
                'threshold': {'line': {'color': "black", 'width': 4}, 'thickness': 0.75, 'value': score}
            }
        ))
        fig.update_layout(height=200, margin=dict(l=20, r=20, t=30, b=20), paper_bgcolor="rgba(0,0,0,0)", font={'color': "white"})
        st.plotly_chart(fig, use_container_width=True)

    with gc2:
        st.markdown(f"""
        <div style="background:rgba(255,255,255,0.05); padding:15px; border-radius:10px; height:100%; display:flex; align-items:center;">
            <div>
                <h4 style="margin:0; color:#f8fafc;">Executive Summary</h4>
                <p style="color:#cbd5e1; font-size:0.95rem; margin-top:5px;">
                    {results.get('summary', 'No summary available.')}
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)

   
    # Section Breakdown Grid
    if "section_analysis" in results:
        st.markdown("#### 🧩 Section Analysis (Grid View)")
        sections = results["section_analysis"]
        
        # Grid Definition
        sec_map = {
            "summary_section": "Summary",
            "experience_section": "Experience", 
            "projects_section": "Projects", 
            "skills_section": "Skills", 
            "education_section": "Education"
        }
        
        cols = st.columns(3)
        
        for i, (key, title) in enumerate(sec_map.items()):
            data = sections.get(key, {})
            sec_score = data.get("score", 0)
            sec_feedback = data.get("feedback", ["No feedback"])[0] if data.get("feedback") else "No feedback"
            
            # Determine color
            if sec_score >= 8: color = "#22c55e" # Green
            elif sec_score >= 5: color = "#f59e0b" # Orange
            else: color = "#ef4444" # Red
            
            with cols[i % 3]:
                st.markdown(f"""
                <div style="background:rgba(30, 41, 59, 0.7); border:1px solid rgba(255,255,255,0.1); border-radius:10px; padding:15px; margin-bottom:15px; position:relative; overflow:hidden;">
                    <div style="position:absolute; top:0; left:0; width:5px; height:100%; background:{color};"></div>
                    <h5 style="margin:0; color:#f1f5f9;">{title}</h5>
                    <div style="font-size:1.5rem; font-weight:700; color:{color};">{sec_score}/10</div>
                    <p style="font-size:0.85rem; color:#94a3b8; margin-top:5px; line-height:1.2;">
                        {sec_feedback[:100] + '...' if len(sec_feedback) > 100 else sec_feedback}
                    </p>
                </div>
                """, unsafe_allow_html=True)

    # 2. Key Strengths
    st.markdown("### 🟢 Key Strengths")
    strengths = results.get("strengths", [])
    if not strengths:
        st.info("No key strengths identified.")
    
    for i, strength in enumerate(strengths):
        st.markdown(f"""
        <div class="insight-card strength-card">
            <div class="insight-title">{i+1}. {strength}</div>
            <div class="insight-meta">
                <div class="meta-item">📁 Category: General</div>
                <div class="meta-item">🔍 Confidence: High</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 3. Key Weaknesses
    st.markdown("### 🔴 Key Weaknesses")
    weaknesses = results.get("weaknesses", [])
    if not weaknesses:
        st.info("No critical weaknesses detected.")

    for i, weakness in enumerate(weaknesses):
        st.markdown(f"""
        <div class="insight-card weakness-card">
            <div class="insight-title">{i+1}. {weakness}</div>
            <div class="insight-meta">
                <div class="meta-item">📁 Category: Skills</div>
                <div class="meta-item badge badge-critical">⚡ Severity: Moderate</div>
            </div>
            <div style="margin-top: 0.8rem; font-size: 0.9rem; color: #4b5563;">
                 📌 <b>Impact:</b> This may affect your ATS score. <br>
                 💡 <b>Suggestion:</b> Consider adding a specific project or certification to address this.
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 4. Improvement Suggestions
    st.markdown("### 🚀 Strategic Improvement Plan")
    suggestions = results.get("improvement_suggestions", [])
    
    if not suggestions:
        st.info("No specific improvements suggested.")
    
    for i, item in enumerate(suggestions):
        impact = item.get('impact', 'Medium')
        suggestion = item.get('suggestion', 'No details available.')
        
        # Determine styling based on impact
        if "High" in impact:
            border_color = "#ef4444" # Red
            bg_color = "rgba(239, 68, 68, 0.1)"
            icon = "🚨"
        elif "Medium" in impact:
            border_color = "#f59e0b" # Orange
            bg_color = "rgba(245, 158, 11, 0.1)"
            icon = "⚠️"
        else:
            border_color = "#3b82f6" # Blue
            bg_color = "rgba(59, 130, 246, 0.1)"
            icon = "💡"
            
        st.markdown(f"""
        <div style="background:{bg_color}; border-left: 5px solid {border_color}; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
            <div style="font-weight: 700; font-size: 1.1rem; color: #f1f5f9; margin-bottom: 5px;">
                {icon} ACTION REQUIRED: {impact.upper()} IMPACT
            </div>
            <div style="font-size: 1rem; color: #e2e8f0; margin-bottom: 10px;">
                {suggestion}
            </div>
            <div style="font-size: 0.9rem; color: #cbd5e1; font-style: italic;">
                <strong>Why this matters:</strong> Addressing this directly correlates to passing initial ATS screening filters and demonstrating core competency.
            </div>
        </div>
        """, unsafe_allow_html=True)

