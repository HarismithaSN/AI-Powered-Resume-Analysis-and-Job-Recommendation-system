import streamlit as st
import time
import json
from backend.scraper import LinkedInScraper, generate_search_query
from backend.llm_analyzer import LLMAnalyzer
from utils.database import save_job_recommendation, get_recommended_jobs, update_job_status, delete_job_recommendation

def render_job_recommendations():
    st.title("💼 Intelligent Job Recommendations")
    st.markdown("---")

    # verify user
    if "user" not in st.session_state:
        st.warning("Please log in to save and track jobs.")
        user_id = 999 # Fallback for demo
    else:
        user_id = st.session_state["user"]["user_id"]

    # -----------------------------
    # Custom CSS
    # -----------------------------
    st.markdown("""
    <style>
    .job-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 20px;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .job-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
        border-color: #475569;
    }
    .match-tag {
        font-weight: 800;
        padding: 6px 12px;
        border-radius: 8px;
        color: white;
    }
    .match-excellent { background-color: #059669; } /* Green */
    .match-good { background-color: #d97706; }      /* Yellow/Orange */
    .match-fair { background-color: #dc2626; }      /* Red */

    .skill-badge {
        display: inline-block;
        padding: 3px 10px;
        margin: 3px;
        border-radius: 99px;
        font-size: 0.75rem;
        background: rgba(255,255,255,0.1);
        border: 1px solid rgba(255,255,255,0.2);
    }
    .badge-missing { border-color: #f87171; color: #f87171; background: rgba(248, 113, 113, 0.1); }
    .badge-check { border-color: #4ade80; color: #4ade80; background: rgba(74, 222, 128, 0.1); }
    
    .score-bar-container {
        width: 100%;
        background-color: #334155;
        height: 8px;
        border-radius: 4px;
        margin-top: 5px;
        margin-bottom: 15px;
    }
    .score-bar-fill {
        height: 100%;
        border-radius: 4px;
    }
    .meta-row {
        display: flex;
        gap: 15px;
        color: #94a3b8;
        font-size: 0.9rem;
        margin-bottom: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

    resume_text = st.session_state.get("resume_text", "")
    
    # -----------------------------
    # Sidebar Filters
    # -----------------------------
    with st.sidebar:
        st.header("🔍 Search Configuration")
        
        # Core Search
        keywords = st.text_input("Keywords", value="Software Engineer")
        location = st.text_input("Location", value="Remote")
        
        st.divider()
        st.subheader("Filters")
        
        job_type = st.selectbox("Job Type", ["Any", "Full-time", "Part-time", "Contract", "Internship"])
        exp_level = st.selectbox("Experience Level", ["Any", "Internship", "Entry level", "Associate", "Mid-Senior level", "Director"])
        date_posted = st.selectbox("Date Posted", ["Any", "Past 24 hours", "Past Week", "Past Month"])
        
        st.divider()
        st.subheader("Results Sorting")
        sort_by = st.selectbox("Sort By", ["Best Match", "Date Posted", "Applicants Count"])
    
    # -----------------------------
    # Main Content
    # -----------------------------
    tab_search, tab_saved = st.tabs(["🔍 Find Jobs", "🔖 Saved Jobs"])
    
    with tab_search:
        render_search_tab(user_id, resume_text, keywords, location, date_posted, job_type, exp_level, sort_by)

    with tab_saved:
        render_saved_jobs_tab(user_id)

def render_search_tab(user_id, resume_text, keywords, location, date_posted, job_type, exp_level, sort_by):
    # Mapping Dropdowns to Scraper Codes
    date_map = {"Past 24 hours": "24h", "Past Week": "week", "Past Month": "month", "Any": None}
    exp_map = {"Any": None, "Internship": "internship", "Entry level": "entry", "Associate": "associate", 
               "Mid-Senior level": "mid-senior", "Director": "director"}
    type_map = {"Any": None, "Full-time": "full-time", "Part-time": "part-time", "Contract": "contract", "Internship": "internship"}

    # Search Button
    if st.button("🔎 Search & Analyze Jobs", type="primary"):
        if not resume_text:
            st.error("Please upload a resume first to enable AI matching.")
        else:
            status_box = st.status("Initializing Job Agent...", expanded=True)
            try:
                scraper = LinkedInScraper(headless=False)
                analyzer = LLMAnalyzer()
                
                # 1. Search
                status_box.write("🌐 Connecting to LinkedIn...")
                scraper.setup_driver()
                scraper.search_jobs(
                    keywords, 
                    location, 
                    date_posted=date_map[date_posted], 
                    experience_level=exp_map[exp_level], 
                    job_type=type_map[job_type]
                )
                
                # 2. Scrape
                status_box.write("📥 Fetching job cards...")
                jobs = scraper.scrape_jobs_listing(limit_pages=1)
                
                if not jobs:
                    status_box.update(label="No jobs found!", state="error")
                    st.error("No jobs found with these criteria.")
                else:
                    status_box.write(f"found {len(jobs)} jobs. Analyzing top 5 matches...")
                    
                    # 3. Analyze Top 5
                    results_for_display = []
                    
                    progress_bar = status_box.progress(0)
                    top_jobs = jobs[:5] # Analyze top 5
                    
                    for i, job in enumerate(top_jobs):
                        status_box.write(f"🧠 AI Analyzing: {job['job_title']} at {job['company_name']}...")
                        
                        # Get full details
                        details = scraper.get_job_details_and_parse(job['job_url'])
                        
                        if details:
                            # AI Weighted Match
                            match_data = analyzer.analyze_match_weighted(resume_text, details.get("job_description", ""))
                            
                            # Merge Data
                            full_job_data = {**job, **details, **match_data}
                            results_for_display.append(full_job_data)
                            
                            # Save to DB
                            save_job_recommendation(
                                user_id=user_id,
                                job_title=full_job_data.get('job_title'),
                                company_name=full_job_data.get('company_name'),
                                location=full_job_data.get('location'),
                                job_description=full_job_data.get('job_description'),
                                job_url=full_job_data.get('job_url'),
                                match_percentage=full_job_data.get('match_score', 0),
                                posted_date=full_job_data.get('posted_date'),
                                salary_range=full_job_data.get('salary_range'),
                                applicants_count=full_job_data.get('applicants_count'),
                                required_skills=full_job_data.get('required_skills'),
                                job_type=full_job_data.get('job_type'),
                                matching_skills=full_job_data.get('matching_skills'),
                                missing_skills=full_job_data.get('missing_skills'),
                                analysis_summary=full_job_data.get('analysis_summary'),
                                component_scores=full_job_data.get('component_scores')
                            )
                        
                        progress_bar.progress((i + 1) / len(top_jobs))
                    
                    st.session_state["analyzed_jobs"] = results_for_display
                    status_box.update(label="Analysis Complete!", state="complete")
                    
                scraper.close()
                st.rerun()
                
            except Exception as e:
                status_box.update(label="Error occurred", state="error")
                st.error(f"Error: {e}")
                if 'scraper' in locals(): scraper.close()

    # -----------------------------
    # Results Display
    # -----------------------------
    # Load from session or DB
    display_jobs = st.session_state.get("analyzed_jobs", [])
    if not display_jobs and user_id != 999:
        # Fallback: Load recent from DB
        display_jobs = get_recommended_jobs(user_id, min_match=0)

    # Sorting Logic (Client side for session data)
    if display_jobs:
        if sort_by == "Best Match":
            display_jobs.sort(key=lambda x: x.get('match_percentage') or 0, reverse=True)
        elif sort_by == "Applicants Count":
            # Simple parsing for sorting
            def parse_applicants(x):
                try: 
                    return int(''.join(filter(str.isdigit, str(x.get('applicants_count', '0')))))
                except: return 0
            display_jobs.sort(key=parse_applicants)
        # Date Posted is tricky without better parsing, skip for now or rely on scraped order

        st.subheader(f"Results ({len(display_jobs)})")
        
        for i, job in enumerate(display_jobs):
            score = job.get('match_percentage') or job.get('match_score') or 0
            
            # Badge Color
            if score >= 85: 
                badge_class = "match-excellent"
                badge_text = "Excellent Match"
            elif score >= 70:
                badge_class = "match-good"
                badge_text = "Good Match"
            else:
                badge_class = "match-fair"
                badge_text = "Fair Match"
                
            # Component Scores
            comps = job.get('component_scores', {})
            s_skill = comps.get('skills', 0) # Max 50
            s_exp = comps.get('experience', 0) # Max 25
            s_edu = comps.get('education', 0) # Max 15
            s_resp = comps.get('responsibility', 0) # Max 10
            
            # Helper for progress bars
            def render_bar(val, max_val, color="#3b82f6"):
                pct = (val / max_val) * 100 if max_val > 0 else 0
                return f"""<div class="score-bar-container"><div class="score-bar-fill" style="width:{pct}%; background-color:{color};"></div></div>"""

            # Skills HTML
            matching = job.get('matching_skills', [])
            missing = job.get('missing_skills', [])
            
            matching_html = "".join([f'<span class="skill-badge badge-check">✓ {s}</span>' for s in matching[:5]])
            missing_html = "".join([f'<span class="skill-badge badge-missing">✗ {s}</span>' for s in missing[:5]])
            
            with st.container():
                st.markdown(f"""
<div class="job-card">
<div style="display:flex; justify-content:space-between;">
<div>
<h3 style="margin:0; color:#f8fafc;">{job.get('job_title', 'Unknown Role')}</h3>
<div style="color:#cbd5e1; font-size:1.1rem; margin-bottom:5px;">{job.get('company_name', 'Unknown Company')}</div>
<div class="meta-row">
<span>📍 {job.get('location', 'Remote')}</span>
<span>📅 {job.get('posted_date', 'Recently')}</span>
<span>👥 {job.get('applicants_count', 'N/A')} applicants</span>
<span>💰 {job.get('salary_range') or 'Salary not listed'}</span>
</div>
</div>
<div style="text-align:right;">
<span class="match-tag {badge_class}">{score}% {badge_text}</span>
<div style="margin-top:10px; display:flex; gap:10px; justify-content:flex-end;">
<a href="{job.get('job_url', '#')}" target="_blank" style="text-decoration:none;">
<button style="background-color:#2563eb; color:white; border:none; padding:8px 16px; border-radius:6px; cursor:pointer; font-weight:600;">Apply ↗</button>
</a>
</div>
</div>
</div>
<hr style="border-color:rgba(255,255,255,0.1); margin: 15px 0;">
<!-- Buttons Row (Streamlit) -->
""", unsafe_allow_html=True)
            
            # Action Buttons below the card content
            c_save, c_apply, c_ignore = st.columns([1, 1, 3])
            with c_save:
                if st.button("🔖 Save Job", key=f"save_{i}"):
                    if job.get('job_id'):
                         update_job_status(job.get('job_id'), 'saved')
                         st.toast("Job Saved!", icon="✅")
                    else:
                        st.error("Save failed (ID missing).")
            
            # Resume content...
            st.markdown(f"""
<!-- Weighted Score Breakdown -->
<div style="display:flex; gap:20px; margin-bottom:15px; background:rgba(0,0,0,0.2); padding:10px; border-radius:8px;">
    <div style="flex:1;">
        <div style="font-size:0.8rem; color:#94a3b8;">Skills (50%)</div>
        {render_bar(s_skill, 50, "#4ade80")}
    </div>
    <div style="flex:1;">
        <div style="font-size:0.8rem; color:#94a3b8;">Experience (25%)</div>
        {render_bar(s_exp, 25, "#60a5fa")}
    </div>
    <div style="flex:1;">
        <div style="font-size:0.8rem; color:#94a3b8;">Education (15%)</div>
        {render_bar(s_edu, 15, "#a78bfa")}
    </div>
     <div style="flex:1;">
        <div style="font-size:0.8rem; color:#94a3b8;">Responsibility (10%)</div>
        {render_bar(s_resp, 10, "#f472b6")}
    </div>
</div>

<!-- AI Analysis -->
<div style="margin-bottom:10px; font-style:italic; color:#e2e8f0;">
     " {job.get('analysis_summary', 'No summary available.')} "
</div>

<div style="display:flex; gap:20px;">
    <div style="flex:1;">
        <strong style="color:#d1d5db; font-size:0.9rem;">✅ Matches</strong><br>
        {matching_html if matching_html else "<span style='color:gray; font-size:0.8rem'>None explicitly detected</span>"}
    </div>
    <div style="flex:1;">
         <strong style="color:#d1d5db; font-size:0.9rem;">⚠️ Missing / To Improve</strong><br>
        {missing_html if missing_html else "<span style='color:gray; font-size:0.8rem'>None explicitly detected</span>"}
    </div>
</div>
</div>
""", unsafe_allow_html=True)

    else:
        st.info("👋 Set your filters on the left and click 'Search' to start finding jobs!")

def render_saved_jobs_tab(user_id):
    st.markdown("### 🔖 Saved Applications")
    
    # Get all jobs and filter in python (since get_recommended_jobs gets all matching)
    # Ideally should add status filter to SQL, but for now filtering here
    all_jobs = get_recommended_jobs(user_id)
    saved_jobs = [j for j in all_jobs if j.get('status') in ['saved', 'applied']]
    
    if not saved_jobs:
        st.info("No saved jobs yet. Go to 'Find Jobs' and save some!")
        return

    for i, job in enumerate(saved_jobs):
        status = job.get('status', 'saved')
        border_color = "#4ade80" if status == 'applied' else "#3b82f6"
        
        with st.expander(f"{'✅' if status=='applied' else '🔖'} {job.get('job_title')} - {job.get('company_name')}", expanded=True):
            st.write(f"**Location:** {job.get('location')}")
            st.write(f"**Match Score:** {job.get('match_percentage')}%")
            
            # Improvement Tip
            missing = job.get('missing_skills', [])
            if missing:
                st.warning(f"**⚠️ Interaction Tip:** You are missing {', '.join(missing[:3])}. Consider highlighting transferable skills in your cover letter.")
            
            col1, col2 = st.columns([1, 4])
            with col1:
                if status != 'applied':
                    if st.button("Mark Applied ✅", key=f"mark_applied_{i}"):
                        update_job_status(job.get('job_id'), 'applied')
                        st.rerun()
                else:
                    st.success("Applied on " + (job.get('posted_date') or "Unknown"))
            
            with col2:
                if st.button("🗑 Remove", key=f"del_{i}"):
                    delete_job_recommendation(job.get('job_id'))
                    st.rerun()
