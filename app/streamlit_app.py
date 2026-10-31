"""
Streamlit Chatbot UI — Multi-Agent Agentic AI Loan Decisioning System
"""
import os
import json
from datetime import datetime, timezone

import streamlit as st
import requests
from dotenv import load_dotenv

load_dotenv()

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Loan Decisioning System",
    page_icon="🏦",
    layout="centered",
)

st.title("🏦 Multi-Agent Agentic AI Loan Decisioning System")
st.caption("Proof of concept — not for production use")

# ---- Initialize chat history ----
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant",
        "content": (
            "Welcome! I'm the Loan Decisioning AI. "
            "Please fill in the loan application form below and click **Submit Application**."
        ),
    })

# ---- Display chat history ----
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---- Loan Application Form ----
with st.expander("📋 Loan Application Form", expanded=True):
    with st.form("loan_form"):
        st.subheader("Applicant Details")
        col1, col2 = st.columns(2)
        with col1:
            applicant_id = st.text_input("Applicant ID *", value="APP001")
            age = st.number_input("Age *", min_value=18, max_value=120, value=35)
            income = st.number_input("Annual Income *", min_value=0.0, value=75000.0, step=1000.0)
        with col2:
            employment_type = st.selectbox(
                "Employment Type *",
                options=["SALARIED", "GOVERNMENT", "SELF_EMPLOYED", "CONTRACT", "PART_TIME", "UNEMPLOYED", "OTHER"],
            )
            location = st.text_input("Location *", value="New York")

        st.subheader("Loan Details")
        col3, col4 = st.columns(2)
        with col3:
            credit_score = st.number_input("Credit Score *", min_value=300, max_value=850, value=720)
            loan_amount = st.number_input("Loan Amount *", min_value=1.0, value=150000.0, step=1000.0)
        with col4:
            tenure = st.number_input("Tenure (months) *", min_value=1, value=36)
            existing_liabilities = st.number_input(
                "Existing Liabilities *", min_value=0.0, value=15000.0, step=1000.0
            )

        submitted = st.form_submit_button("Submit Application", type="primary")


def _render_result(data: dict):
    classification = data.get("classification", "Unknown")
    risk_score = data.get("risk_score", 0)
    confidence = data.get("confidence_level", 0)
    factors = data.get("key_decision_factors", [])
    explanation = data.get("explanation", "")
    action_taken = data.get("action_taken", "")
    case_id = data.get("case_id", "")
    timestamp = data.get("timestamp", "")
    summary = data.get("summary", "")
    mock_mode = data.get("mock_mode", False)

    # Classification badge
    badge_color = {"Approved": "green", "Rejected": "red", "Requires Manual Review": "orange"}
    color = badge_color.get(classification, "gray")

    mock_notice = " *(Mock LLM Mode)*" if mock_mode else ""

    response_text = (
        f"### Decision: :{color}[**{classification}**]{mock_notice}\n\n"
        f"| Field | Value |\n|---|---|\n"
        f"| **Risk Score** | {risk_score:.1f} / 100 |\n"
        f"| **Confidence Level** | {confidence:.0%} |\n"
        f"| **Case ID** | `{case_id}` |\n"
        f"| **Timestamp** | {timestamp} |\n\n"
        f"**Key Decision Factors:**\n"
        + "".join(f"- {f}\n" for f in factors)
        + f"\n**Explanation:**\n{explanation}\n\n"
        f"**Action Summary:**\n{action_taken}\n\n"
        f"**Summary:**\n{summary}"
    )

    st.markdown(response_text)
    st.session_state.messages.append({"role": "assistant", "content": response_text})


def _render_validation_error(detail):
    msg = f"**Validation Error**\n\n{detail}"
    st.error(msg)
    st.session_state.messages.append({"role": "assistant", "content": f"❌ {msg}"})


def _render_server_error(status_code: int, body: str):
    msg = f"**Server Error (HTTP {status_code})**\n\n{body}"
    st.error(msg)
    st.session_state.messages.append({"role": "assistant", "content": f"❌ {msg}"})


def _render_connection_error():
    msg = (
        "**Cannot connect to the loan decisioning service.**\n\n"
        f"Please ensure the FastAPI microservice is running at `{FASTAPI_URL}`.\n\n"
        "Start it with: `uvicorn microservice.main:app --reload --port 8000`"
    )
    st.error(msg)
    st.session_state.messages.append({"role": "assistant", "content": f"⚠️ {msg}"})


# ---- Handle form submission ----
if submitted:
    # Basic client-side validation
    if not applicant_id.strip():
        st.error("Applicant ID is required.")
    elif not location.strip():
        st.error("Location is required.")
    else:
        # Add user message to chat
        user_msg = (
            f"**Loan Application Submitted**\n\n"
            f"- **Applicant ID:** {applicant_id}\n"
            f"- **Age:** {age}\n"
            f"- **Income:** {income:,.2f}\n"
            f"- **Employment Type:** {employment_type}\n"
            f"- **Credit Score:** {credit_score}\n"
            f"- **Loan Amount:** {loan_amount:,.2f}\n"
            f"- **Tenure:** {tenure} months\n"
            f"- **Existing Liabilities:** {existing_liabilities:,.2f}\n"
            f"- **Location:** {location}"
        )
        st.session_state.messages.append({"role": "user", "content": user_msg})

        with st.chat_message("user"):
            st.markdown(user_msg)

        # Processing indicator
        with st.chat_message("assistant"):
            with st.spinner("🔄 Processing application through AI agents..."):
                payload = {
                    "applicant_id": applicant_id.strip(),
                    "applicant_profile": {
                        "age": int(age),
                        "income": float(income),
                        "employment_type": employment_type,
                    },
                    "credit_score": int(credit_score),
                    "loan_amount": float(loan_amount),
                    "tenure": int(tenure),
                    "existing_liabilities": float(existing_liabilities),
                    "location": location.strip(),
                    "application_timestamp": datetime.now(timezone.utc).isoformat(),
                }

                try:
                    resp = requests.post(
                        f"{FASTAPI_URL}/loan/apply",
                        json=payload,
                        timeout=60,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        _render_result(data)
                    elif resp.status_code == 422:
                        error_detail = resp.json().get("detail", "Validation error")
                        _render_validation_error(error_detail)
                    else:
                        _render_server_error(resp.status_code, resp.text)
                except requests.exceptions.ConnectionError:
                    _render_connection_error()
                except Exception as exc:
                    st.error(f"Unexpected error: {exc}")
