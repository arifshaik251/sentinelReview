import logging
import sys
import os

import streamlit as st
from dotenv import load_dotenv

# Ensure project root is on the path so `agents` resolves.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.orchestrator import Orchestrator

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

SAMPLE_CODE = '''\
import os, sqlite3

DB_PASSWORD = "super_secret_123"
API_KEY = "AKIAIOSFODNN7EXAMPLE"

def get_user(username):
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE name = '{username}'"
    cursor.execute(query)
    return cursor.fetchone()

def run_command(user_input):
    os.system(f"echo {user_input}")
'''

# ── Streamlit UI ──────────────────────────────────────────────

st.set_page_config(page_title="SentinelReview", page_icon="🛡️", layout="wide")

st.title("🛡️ SentinelReview")
st.caption("Multi-agent code review: guardrails → quality + security → unified report")

# Sidebar settings
with st.sidebar:
    st.header("⚙️ Settings")
    api_key = st.text_input("Anthropic API Key", type="password", value=os.getenv("ANTHROPIC_API_KEY", ""))
    model = st.selectbox(
        "Model",
        [
            "claude-sonnet-4-5",
            "claude-haiku-4-5",
            "claude-3-7-sonnet-20250219",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
        ],
        index=0,
    )
    parallel = st.checkbox("Run reviewer & auditor in parallel", value=True)
    st.divider()
    st.markdown(
        "**Pipeline:**\n"
        "1. 🔒 Guardrail — secret scan + safety check\n"
        "2. 📝 Code Review + 🛡️ Security Audit (parallel)\n"
        "3. 📊 Synthesizer — unified report"
    )

code_input = st.text_area(
    "Paste your code here",
    value=SAMPLE_CODE,
    height=300,
    help="Paste any code snippet for multi-agent review.",
)

run_clicked = st.button("🚀 Run Review", type="primary", use_container_width=True)

if run_clicked:
    if not code_input.strip():
        st.error("Please paste some code to review.")
        st.stop()

    if not api_key:
        st.error("Please provide an Anthropic API key in the sidebar.")
        st.stop()

    os.environ["ANTHROPIC_API_KEY"] = api_key

    orchestrator = Orchestrator(model=model, parallel=parallel)

    with st.status("Running multi-agent pipeline…", expanded=True) as status:
        st.write("🔒 Running guardrail pre-screening…")
        guardrail_result = orchestrator._guardrail.run(code_input)

        st.write("📝 Running code review & 🛡️ security audit…")
        if parallel:
            review_result, audit_result = orchestrator._run_parallel(code_input)
        else:
            review_result, audit_result = orchestrator._run_sequential(code_input)

        st.write("📊 Synthesizing final report…")
        review_text = review_result.review_text if not review_result.error else f"[Error] {review_result.error}"
        audit_text = audit_result.audit_text if not audit_result.error else f"[Error] {audit_result.error}"
        synthesis_result = orchestrator._synthesizer.run(
            guardrail_summary=guardrail_result.summary,
            review_text=review_text,
            audit_text=audit_text,
        )
        status.update(label="✅ Pipeline complete", state="complete")

    # ── Display results in tabs ──
    tab_synth, tab_guard, tab_review, tab_audit = st.tabs(
        ["📊 Unified Report", "🔒 Guardrail", "📝 Code Review", "🛡️ Security Audit"]
    )

    with tab_synth:
        if synthesis_result.error:
            st.error(synthesis_result.error)
        else:
            st.markdown(synthesis_result.report)

    with tab_guard:
        if guardrail_result.passed:
            st.success("No hardcoded secrets detected.")
        else:
            st.warning(f"Found {len(guardrail_result.secrets_found)} potential secret(s)")
        st.markdown(guardrail_result.summary)

    with tab_review:
        if review_result.error:
            st.error(review_result.error)
        else:
            st.markdown(review_result.review_text)

    with tab_audit:
        if audit_result.error:
            st.error(audit_result.error)
        else:
            st.markdown(audit_result.audit_text)
