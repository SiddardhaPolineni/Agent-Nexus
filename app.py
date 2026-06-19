import streamlit as st
import requests
import uuid
import os
import pandas as pd
import json
from datetime import datetime

# --- Config ---
API_URL = "http://localhost:8000"
UPLOAD_DIR = "data/resumes"
JOB_TRACKER_FILE = "data/job_tracker.csv"
PORTFOLIO_FILE = "data/portfolio.csv"

os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- Session State ---
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "waiting_for_input" not in st.session_state:
    st.session_state.waiting_for_input = False

# --- Page Config ---
st.set_page_config(page_title="Agent Nexus", page_icon="🤖", layout="wide")

# --- Greeting ---
def get_greeting():
    hour = datetime.now().hour
    if hour < 12:
        return "Good Morning"
    elif hour < 17:
        return "Good Afternoon"
    else:
        return "Good Evening"

# --- Heavy CSS ---
st.markdown("""
<style>
    /* ===== MAIN HEADER ===== */
    .main-header {
        text-align: center;
        padding: 1.5rem 0 1rem 0;
    }
    
    /* Chat font size */
    .stChatMessage p, .stChatMessage li, .stChatMessage span {
        font-size: 1.1rem !important;
        line-height: 1.7 !important;
    }
    .stChatMessage h1, .stChatMessage h2, .stChatMessage h3 {
        font-size: 1.3rem !important;
    }
    .stChatMessage code {
        font-size: 1rem !important;
    }
    
    /* Chat input font */
    div[data-testid="stChatInput"] textarea {
        font-size: 1.05rem !important;
    }
    
    /* ===== AGENT BADGES ===== */
    .agent-badges {
        display: flex;
        justify-content: center;
        gap: 0.8rem;
        margin-top: 0.5rem;
    }
    .agent-badge {
        padding: 0.4rem 1rem;
        border-radius: 2rem;
        font-size: 0.8rem;
        font-weight: 600;
        border: 1px solid;
    }
    .badge-job { 
        background: rgba(59,130,246,0.1); 
        color: #2563eb; 
        border-color: rgba(59,130,246,0.3);
    }
    .badge-news { 
        background: rgba(16,185,129,0.1); 
        color: #059669; 
        border-color: rgba(16,185,129,0.3);
    }
    .badge-finance { 
        background: rgba(245,158,11,0.1); 
        color: #d97706; 
        border-color: rgba(245,158,11,0.3);
    }

    /* ===== SIDEBAR ===== */
    section[data-testid="stSidebar"],
    section[data-testid="stSidebar"] > div,
    div[data-testid="stSidebar"],
    div[data-testid="stSidebar"] > div:first-child {
        background: #f8f9fb !important;
        border-right: 1px solid #e5e7eb !important;
    }
    
    /* All sidebar text */
    div[data-testid="stSidebar"] p,
    div[data-testid="stSidebar"] span,
    div[data-testid="stSidebar"] label,
    div[data-testid="stSidebar"] li {
        color: #374151 !important;
        font-size: 1rem;
    }
    
    /* Dividers */
    div[data-testid="stSidebar"] hr {
        border: none !important;
        border-top: 1px solid #e5e7eb !important;
        margin: 1.5rem 0 !important;
    }
    
    /* Sidebar brand title */
    .sidebar-brand {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        padding: 0.2rem 0 1rem 0;
        border-bottom: 1px solid #e5e7eb;
        margin-bottom: 1rem;
    }
    .sidebar-brand .logo {
        width: 32px;
        height: 32px;
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1rem;
    }
    .sidebar-brand .name {
        font-size: 1.1rem;
        font-weight: 700;
        color: #111827 !important;
        letter-spacing: -0.3px;
    }
    
    /* Section labels */
    .section-label {
        font-size: 0.85rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #6366f1 !important;
        padding: 0.5rem 0.8rem;
        margin-top: 0.5rem;
        margin-bottom: 0.3rem;
        background: #eef2ff;
        border-radius: 6px;
        border-left: 3px solid #6366f1;
    }
    
    /* New Chat button - force override all Streamlit button styles */
    div[data-testid="stSidebar"] button {
        background: #6366f1 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.7rem 1.2rem !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        transition: all 0.15s ease;
        box-shadow: 0 2px 6px rgba(99,102,241,0.3);
    }
    div[data-testid="stSidebar"] button:hover {
        background: #4f46e5 !important;
        box-shadow: 0 4px 10px rgba(99,102,241,0.4);
    }
    
    /* Upload button - override with green (higher specificity) */
    section[data-testid="stSidebar"] [data-testid="stFileUploader"] button,
    div[data-testid="stSidebar"] [data-testid="stFileUploader"] button,
    [data-testid="stSidebar"] [data-testid="stFileUploader"] button {
        background: #10b981 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 700 !important;
        font-size: 0.9rem !important;
        padding: 0.5rem 1rem !important;
        box-shadow: 0 2px 6px rgba(16,185,129,0.3) !important;
    }
    section[data-testid="stSidebar"] [data-testid="stFileUploader"] button:hover,
    div[data-testid="stSidebar"] [data-testid="stFileUploader"] button:hover {
        background: #059669 !important;
        box-shadow: 0 4px 10px rgba(16,185,129,0.4) !important;
    }
    div[data-testid="stSidebar"] [data-testid="stFileUploader"] small {
        color: #9ca3af !important;
        font-size: 0.8rem !important;
    }
    
    /* Selectbox dropdown - fix visibility */
    div[data-testid="stSidebar"] [data-testid="stSelectbox"] {
        color: #374151 !important;
    }
    div[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div {
        background: #ffffff !important;
        border: 2px solid #6366f1 !important;
        border-radius: 8px !important;
        color: #374151 !important;
        font-size: 0.95rem !important;
    }
    div[data-testid="stSidebar"] [data-testid="stSelectbox"] svg {
        fill: #374151 !important;
    }
    div[data-testid="stSidebar"] [data-testid="stSelectbox"] input {
        color: #374151 !important;
    }
    div[data-testid="stSidebar"] [role="listbox"] {
        background: #ffffff !important;
        border: 1px solid #d1d5db !important;
    }
    div[data-testid="stSidebar"] [role="option"] {
        color: #374151 !important;
    }
    div[data-testid="stSidebar"] [role="option"]:hover {
        background: #eef2ff !important;
    }
    
    /* Metrics */
    div[data-testid="stSidebar"] [data-testid="stMetricValue"] {
        color: #111827 !important;
        font-size: 1.4rem !important;
        font-weight: 700 !important;
    }
    div[data-testid="stSidebar"] [data-testid="stMetricLabel"] {
        color: #9ca3af !important;
        font-size: 0.7rem !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Quick prompt buttons - outlined style */
    div[data-testid="stSidebar"] button[kind="secondary"] {
        background: #ffffff !important;
        color: #374151 !important;
        border: 1px solid #d1d5db !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        text-align: left !important;
        box-shadow: none !important;
    }
    div[data-testid="stSidebar"] button[kind="secondary"]:hover {
        background: #eef2ff !important;
        border-color: #6366f1 !important;
        color: #4f46e5 !important;
        box-shadow: none !important;
    }
    
    /* Info/alert in sidebar */
    div[data-testid="stSidebar"] .stAlert {
        background: #ffffff !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 8px !important;
        padding: 0.6rem 0.8rem !important;
    }
    div[data-testid="stSidebar"] .stAlert p {
        color: #6b7280 !important;
        font-size: 0.9rem !important;
    }
    
    /* Dataframe */
    div[data-testid="stSidebar"] .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #e5e7eb;
    }

    /* ===== WELCOME CARD ===== */
    .welcome-card {
        background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%);
        border: 1px solid rgba(99,102,241,0.2);
        border-radius: 20px;
        padding: 2.5rem;
        text-align: center;
        margin: 1.5rem 0 2rem 0;
    }
    .welcome-card h2 {
        margin: 0 0 0.5rem 0;
        font-size: 2rem;
        color: #312e81;
    }
    .welcome-card p {
        margin: 0;
        color: #4338ca;
        font-size: 1rem;
        line-height: 1.6;
    }
    .welcome-features {
        display: flex;
        justify-content: center;
        gap: 1.2rem;
        margin-top: 2rem;
        flex-wrap: wrap;
    }
    .welcome-feature {
        background: white;
        border: 1px solid rgba(99,102,241,0.15);
        border-radius: 16px;
        padding: 1.2rem 1.5rem;
        text-align: center;
        min-width: 180px;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(99,102,241,0.08);
    }
    .welcome-feature:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(99,102,241,0.15);
    }
    .welcome-feature .icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }
    .welcome-feature .label {
        font-size: 0.85rem;
        color: #4338ca;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown("""
<div class="main-header">
    <div style="display:flex;align-items:center;justify-content:center;gap:0.6rem;">
        <img src="https://img.icons8.com/fluency/48/artificial-intelligence.png" width="36"/>
        <h1 style="margin:0;font-size:2rem;">Agent Nexus</h1>
    </div>
    <div class="agent-badges">
        <span class="agent-badge badge-job">💼 Job Search</span>
        <span class="agent-badge badge-news">📰 AI News</span>
        <span class="agent-badge badge-finance">💰 Finance</span>
    </div>
</div>
""", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <img src="https://img.icons8.com/fluency/48/artificial-intelligence.png" width="28"/>
        <span class="name"><h1>Agent Nexus</h1></span>
    </div>
    """, unsafe_allow_html=True)

    if st.button("＋  New Chat", use_container_width=True, type="primary"):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.session_state.waiting_for_input = False
        st.session_state.pop("resume_path", None)
        st.session_state.pop("resume_skills", None)
        st.session_state.pop("resume_file", None)
        st.session_state["uploader_key"] = str(uuid.uuid4())
        st.rerun()

    st.divider()

    # Resume Upload
    st.markdown('<div class="section-label">Resume</div>', unsafe_allow_html=True)
    uploader_key = st.session_state.get("uploader_key", "default_uploader")
    uploaded_file = st.file_uploader("Drop your resume here", type=["pdf"], label_visibility="collapsed", key=uploader_key)

    if uploaded_file:
        file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"✓ {uploaded_file.name}")
        st.session_state["resume_path"] = file_path
        
        # Extract skills silently (cached)
        if "resume_skills" not in st.session_state or st.session_state.get("resume_file") != uploaded_file.name:
            import sys
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from src.tools.resume_parser import extract_text_from_pdf, extract_skills_from_resume
            with st.spinner("Processing resume..."):
                resume_text = extract_text_from_pdf(file_path)
                skills_str = extract_skills_from_resume(resume_text)
                st.session_state["resume_skills"] = [s.strip() for s in skills_str.split(",")]
                st.session_state["resume_file"] = uploaded_file.name

    st.divider()

    # Trackers
    st.markdown('<div class="section-label">Trackers</div>', unsafe_allow_html=True)
    tracker_tab = st.selectbox("Select tracker:", ["Select tracker type", "Job Tracker", "Portfolio"], label_visibility="collapsed")

    if tracker_tab == "Job Tracker":
        if os.path.exists(JOB_TRACKER_FILE):
            df = pd.read_csv(JOB_TRACKER_FILE)
            st.dataframe(
                df[["job_title", "company", "status"]],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No jobs tracked yet.")

    elif tracker_tab == "Portfolio":
        if os.path.exists(PORTFOLIO_FILE):
            df = pd.read_csv(PORTFOLIO_FILE)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No portfolios saved yet.")

    st.divider()
    st.markdown('<div class="section-label">Try these</div>', unsafe_allow_html=True)
    
    quick_prompts = [
        "Find me ML engineer jobs in NYC",
        "Latest news on AI agents",
        "Build a high-risk portfolio with $5000"
    ]
    
    for qp in quick_prompts:
        if st.button(qp, key=f"qp_{qp}", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": qp})
            # Trigger chat by storing in session and rerunning
            st.session_state["pending_prompt"] = qp
            st.rerun()

# --- Welcome Message ---
if not st.session_state.messages:
    greeting = get_greeting()
    st.markdown(f"""
    <div class="welcome-card">
        <h2>{greeting}! 👋</h2>
        <p>I'm <strong>Agent Nexus</strong> — your AI-powered multi-agent assistant.<br/>
        I orchestrate specialized agents to help you with career, knowledge, and wealth.</p>
        <div class="welcome-features">
            <div class="welcome-feature">
                <div class="icon">💼</div>
                <div class="label">Find jobs & track applications</div>
            </div>
            <div class="welcome-feature">
                <div class="icon">📰</div>
                <div class="label">Latest AI news & insights</div>
            </div>
            <div class="welcome-feature">
                <div class="icon">💰</div>
                <div class="label">Build & manage portfolios</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- Chat Display ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Human-in-the-Loop ---
if st.session_state.waiting_for_input:
    st.divider()
    st.warning("⏸️ Agent is waiting for your approval to proceed.")

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("✅ Approve", use_container_width=True, type="primary"):
            with st.spinner("Processing..."):
                full_response = ""
                with requests.post(f"{API_URL}/resume/stream", json={
                    "thread_id": st.session_state.thread_id,
                    "feedback": "yes"
                }, stream=True, timeout=120) as response:
                    for line in response.iter_lines(decode_unicode=True):
                        if line and line.startswith("data: "):
                            data = json.loads(line[6:])
                            if data.get("node") == "done":
                                break
                            if data.get("content"):
                                full_response = data["content"]
                if full_response:
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                st.session_state.waiting_for_input = False
                st.rerun()
    with col2:
        if st.button("❌ Reject", use_container_width=True):
            with st.spinner("Processing..."):
                full_response = ""
                with requests.post(f"{API_URL}/resume/stream", json={
                    "thread_id": st.session_state.thread_id,
                    "feedback": "no"
                }, stream=True, timeout=120) as response:
                    for line in response.iter_lines(decode_unicode=True):
                        if line and line.startswith("data: "):
                            data = json.loads(line[6:])
                            if data.get("node") == "done":
                                break
                            if data.get("content"):
                                full_response = data["content"]
                if full_response:
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                st.session_state.waiting_for_input = False
                st.rerun()
    with col3:
        feedback = st.text_input("Or provide specific feedback:", placeholder="e.g., change allocation to 60% stocks")
        if feedback:
            if st.button("📝 Send", use_container_width=True):
                with st.spinner("Processing..."):
                    full_response = ""
                    with requests.post(f"{API_URL}/resume/stream", json={
                        "thread_id": st.session_state.thread_id,
                        "feedback": feedback
                    }, stream=True, timeout=120) as response:
                        for line in response.iter_lines(decode_unicode=True):
                            if line and line.startswith("data: "):
                                data = json.loads(line[6:])
                                if data.get("node") == "done":
                                    break
                                if data.get("content"):
                                    full_response = data["content"]
                    if full_response:
                        st.session_state.messages.append({"role": "assistant", "content": full_response})
                    st.session_state.waiting_for_input = False
                    st.rerun()

# --- Handle quick prompt clicks ---
if "pending_prompt" in st.session_state:
    prompt = st.session_state.pop("pending_prompt")
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        status_placeholder = st.empty()
        status_placeholder.markdown("⏳ *Analyzing your request...*")
        full_response = ""
        waiting = False
        try:
            with requests.post(
                f"{API_URL}/chat/stream",
                json={"message": prompt, "thread_id": st.session_state.thread_id},
                stream=True,
                timeout=120
            ) as response:
                for line in response.iter_lines(decode_unicode=True):
                    if line and line.startswith("data: "):
                        data = json.loads(line[6:])
                        node = data.get("node", "")
                        content = data.get("content", "")
                        if node == "done":
                            break
                        elif node == "interrupt":
                            waiting = True
                            break
                        elif content:
                            status_placeholder.empty()
                            if node == "supervisor":
                                response_placeholder.markdown("🧠 *Routing to the right agent...*")
                            else:
                                full_response = content
                                response_placeholder.markdown(full_response)
                        else:
                            node_status = {
                                "guardrail": "🛡️ *Analyzing...*",
                                "supervisor": "🧠 *Processing...*",
                                "job_search": "💼 *Searching job listings...*",
                                "ai_news": "📰 *Fetching latest news...*",
                                "finance": "💰 *Analyzing market data...*",
                                "general": "💭 *Composing response...*",
                            }
                            status_placeholder.markdown(node_status.get(node, "⚙️ *Processing...*"))
            if full_response:
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            if waiting:
                st.session_state.waiting_for_input = True
                st.rerun()
        except Exception as e:
            st.error(f"Something went wrong: {str(e)}")

# --- Chat Input ---
if prompt := st.chat_input("Ask me anything — jobs, AI news, or finance...", disabled=st.session_state.waiting_for_input):
    # Store the clean prompt for display
    display_prompt = prompt
    
    # Only append resume skills if the query seems job-related
    job_keywords = ["job", "jobs", "role", "roles", "resume", "career", "position", "hiring", "apply", "score", "match", "skills", "engineer", "developer"]
    if "resume_skills" in st.session_state and any(kw in prompt.lower() for kw in job_keywords):
        skills_str = ", ".join(st.session_state["resume_skills"])
        prompt += f"\n\n[User's resume skills: {skills_str}. Based on these skills from the user's resume, find relevant jobs. Mention that these results are based on their resume skills.]"

    # Display user message (clean, without skills)
    st.session_state.messages.append({"role": "user", "content": display_prompt})
    with st.chat_message("user"):
        st.markdown(display_prompt)

    # Call streaming API
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        status_placeholder = st.empty()
        status_placeholder.markdown("⏳ *Analyzing your request...*")
        full_response = ""
        waiting = False

        try:
            with requests.post(
                f"{API_URL}/chat/stream",
                json={"message": prompt, "thread_id": st.session_state.thread_id},
                stream=True,
                timeout=120
            ) as response:
                for line in response.iter_lines(decode_unicode=True):
                    if line and line.startswith("data: "):
                        data = json.loads(line[6:])

                        node = data.get("node", "")
                        content = data.get("content", "")

                        if node == "done":
                            break
                        elif node == "interrupt":
                            waiting = True
                            break
                        elif content:
                            status_placeholder.empty()
                            if node == "supervisor":
                                response_placeholder.markdown("🧠 *Routing to the right agent...*")
                            else:
                                full_response = content
                                response_placeholder.markdown(full_response)
                        else:
                            # Update status based on which node is running
                            node_status = {
                                "guardrail": "🛡️ *Checking safety...*",
                                "supervisor": "🧠 *Understanding your intent...*",
                                "job_search": "💼 *Searching job listings...*",
                                "ai_news": "📰 *Fetching latest news...*",
                                "finance": "💰 *Analyzing market data...*",
                                "general": "💭 *Composing response...*",
                            }
                            status_msg = node_status.get(node, "⚙️ *Processing...*")
                            status_placeholder.markdown(status_msg)

            if full_response:
                st.session_state.messages.append({"role": "assistant", "content": full_response})

            if waiting:
                st.session_state.waiting_for_input = True
                st.rerun()

        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to the API. Make sure the backend is running: `uvicorn api:app --reload --port 8000`")
        except requests.exceptions.Timeout:
            st.error("⏱️ Request timed out. The agent might be processing a complex query.")
        except Exception as e:
            st.error(f"Something went wrong: {str(e)}")
