"""
Tests for the four agents and their output schemas.
Uses mock HTTP calls to MCP servers.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from models.loan_application import LoanApplication, ApplicantProfile
from models.agent_outputs import (
    ApplicantProfileOutput,
    FinancialRiskOutput,
    LoanDecisionOutput,
    ComplianceActionOutput,
)
from tests.conftest import make_application


# ---- Mocked MCP responses ----

MOCK_APPLICANT_CTX = {
    "applicant_id": "TEST001",
    "credit_history": "No defaults.",
    "previous_loans": 2,
    "previous_defaults": 0,
    "years_at_current_employment": 5,
    "income_verification_status": "Verified",
    "income_stability_indicators": ["High income bracket", "Stable employment type"],
    "completeness_issues": [],
}

MOCK_RISK_RULES = {
    "rule_category": "all",
    "disclaimer": "POC rules",
    "rules": {
        "dti": {"low_risk_max": 0.30, "medium_risk_max": 0.50},
        "credit_score": {"excellent_min": 750, "good_min": 650, "fair_min": 550},
        "loan_amount": {"low_risk_max": 100000, "medium_risk_max": 500000},
        "anomaly": {"loan_to_income_ratio_max": 10.0, "age_min": 18, "age_max": 75, "tenure_min": 6},
        "income": {"high_stability_min": 80000, "medium_stability_min": 40000},
        "employment": {},
        "decision": {
            "credit_score_weight": 0.35,
            "dti_weight": 0.30,
            "loan_amount_weight": 0.20,
            "employment_weight": 0.15,
            "approved_max_risk": 35,
            "manual_review_max_risk": 65,
        },
    }
}

MOCK_SYNTHESIS = {
    "risk_score": 25.0,
    "confidence_level": 0.88,
    "preliminary_classification": "Approved",
    "key_decision_factors": ["Good credit score"],
    "synthesis_context": "Risk Score: 25.0/100",
}

MOCK_NOTIFICATION = {
    "action_taken": "Loan approval letter prepared.",
    "notification_sent": True,
    "case_id": "CASE-ABCD1234",
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "summary": "Application TEST001 APPROVED.",
}


def _mock_post(url, json=None, timeout=None):
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    if "get_applicant_context" in url:
        mock_resp.json.return_value = MOCK_APPLICANT_CTX
    elif "get_risk_rules" in url:
        mock_resp.json.return_value = MOCK_RISK_RULES
    elif "synthesize_decision" in url:
        mock_resp.json.return_value = MOCK_SYNTHESIS
    elif "send_notification" in url:
        mock_resp.json.return_value = MOCK_NOTIFICATION
    return mock_resp


# ---- Test 10: Applicant Profile Agent output ----
@patch("httpx.post", side_effect=_mock_post)
def test_applicant_profile_agent_output(mock_http):
    from agents.applicant_profile_agent import run_applicant_profile_agent
    app = make_application()
    result = run_applicant_profile_agent(app)
    assert isinstance(result, ApplicantProfileOutput)
    assert 0 <= result.income_stability_score <= 100
    assert result.employment_risk in ("Low", "Medium", "High")
    assert isinstance(result.credit_history_summary, str)
    assert isinstance(result.application_completeness_flags, list)


# ---- Test 11: Financial Risk Analysis Agent output ----
@patch("httpx.post", side_effect=_mock_post)
def test_financial_risk_analysis_agent_output(mock_http):
    from agents.financial_risk_analysis_agent import run_financial_risk_analysis_agent
    app = make_application()
    result = run_financial_risk_analysis_agent(app)
    assert isinstance(result, FinancialRiskOutput)
    assert result.debt_to_income_ratio >= 0
    assert result.credit_score_risk_level in ("Excellent", "Good", "Fair", "Poor")
    assert result.loan_amount_risk in ("Low", "Medium", "High")
    assert isinstance(result.anomaly_detection, str)
    assert isinstance(result.reasoning, str)


# ---- Test 8: Debt-to-Income Ratio calculation ----
@patch("httpx.post", side_effect=_mock_post)
def test_dti_ratio_calculation(mock_http):
    from agents.financial_risk_analysis_agent import run_financial_risk_analysis_agent
    app = make_application(
        applicant_profile=ApplicantProfile(age=35, income=50000.0, employment_type="SALARIED"),
        existing_liabilities=15000.0,
    )
    result = run_financial_risk_analysis_agent(app)
    expected_dti = 15000.0 / 50000.0
    assert abs(result.debt_to_income_ratio - expected_dti) < 0.001


# ---- Test 9: Zero-income handling ----
@patch("httpx.post", side_effect=_mock_post)
def test_zero_income_handling(mock_http):
    from agents.financial_risk_analysis_agent import run_financial_risk_analysis_agent
    app = make_application(
        applicant_profile=ApplicantProfile(age=35, income=0.0, employment_type="UNEMPLOYED"),
        existing_liabilities=5000.0,
    )
    result = run_financial_risk_analysis_agent(app)
    assert result.debt_to_income_ratio == 0.0
    assert "zero" in result.reasoning.lower() or "income" in result.reasoning.lower()


# ---- Test 12: Approved classification (mock LLM) ----
@patch("httpx.post", side_effect=_mock_post)
def test_loan_decision_approved(mock_http):
    from agents.loan_decision_agent import run_loan_decision_agent
    import os
    os.environ["MOCK_LLM_MODE"] = "true"
    profile = ApplicantProfileOutput(
        income_stability_score=85.0,
        employment_risk="Low",
        credit_history_summary="No defaults.",
        application_completeness_flags=[],
    )
    risk = FinancialRiskOutput(
        debt_to_income_ratio=0.20,
        credit_score_risk_level="Excellent",
        loan_amount_risk="Low",
        anomaly_detection="No anomalies detected",
        reasoning="All good.",
    )
    app = make_application()
    result = run_loan_decision_agent(app, profile, risk)
    assert isinstance(result, LoanDecisionOutput)
    assert result.classification in ("Approved", "Rejected", "Requires Manual Review")
    assert 0 <= result.risk_score <= 100
    assert 0 <= result.confidence_level <= 1


# ---- Test 13: Rejected classification (high-risk inputs) ----
@patch("httpx.post")
def test_loan_decision_rejected(mock_post):
    from agents.loan_decision_agent import run_loan_decision_agent
    import os
    os.environ["MOCK_LLM_MODE"] = "true"

    high_risk_synthesis = {
        "risk_score": 85.0,
        "confidence_level": 0.90,
        "preliminary_classification": "Rejected",
        "key_decision_factors": ["Very poor credit score", "High DTI"],
        "synthesis_context": "Risk Score: 85.0/100",
    }
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = high_risk_synthesis
    mock_post.return_value = resp

    profile = ApplicantProfileOutput(
        income_stability_score=10.0,
        employment_risk="High",
        credit_history_summary="Multiple defaults.",
        application_completeness_flags=[],
    )
    risk = FinancialRiskOutput(
        debt_to_income_ratio=0.90,
        credit_score_risk_level="Poor",
        loan_amount_risk="High",
        anomaly_detection="High DTI anomaly",
        reasoning="Very high risk.",
    )
    app = make_application(
        applicant_profile=ApplicantProfile(age=28, income=20000.0, employment_type="UNEMPLOYED"),
        credit_score=380,
        loan_amount=800000.0,
    )
    result = run_loan_decision_agent(app, profile, risk)
    assert result.classification == "Rejected"


# ---- Test 14: Requires Manual Review classification ----
@patch("httpx.post")
def test_loan_decision_requires_manual_review(mock_post):
    from agents.loan_decision_agent import run_loan_decision_agent
    import os
    os.environ["MOCK_LLM_MODE"] = "true"

    manual_synthesis = {
        "risk_score": 50.0,
        "confidence_level": 0.60,
        "preliminary_classification": "Requires Manual Review",
        "key_decision_factors": ["Borderline credit score"],
        "synthesis_context": "Risk Score: 50.0/100",
    }
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = manual_synthesis
    mock_post.return_value = resp

    profile = ApplicantProfileOutput(
        income_stability_score=55.0,
        employment_risk="Medium",
        credit_history_summary="One late payment.",
        application_completeness_flags=[],
    )
    risk = FinancialRiskOutput(
        debt_to_income_ratio=0.40,
        credit_score_risk_level="Fair",
        loan_amount_risk="Medium",
        anomaly_detection="No anomalies detected",
        reasoning="Borderline.",
    )
    app = make_application(
        applicant_profile=ApplicantProfile(age=42, income=55000.0, employment_type="SELF_EMPLOYED"),
        credit_score=610,
        loan_amount=200000.0,
    )
    result = run_loan_decision_agent(app, profile, risk)
    assert result.classification == "Requires Manual Review"


# ---- Test 18: Mock LLM mode ----
@patch("httpx.post", side_effect=_mock_post)
def test_mock_llm_mode_produces_valid_output(mock_http):
    from agents.loan_decision_agent import run_loan_decision_agent
    import os
    os.environ["MOCK_LLM_MODE"] = "true"
    profile = ApplicantProfileOutput(
        income_stability_score=70.0,
        employment_risk="Low",
        credit_history_summary="Good standing.",
        application_completeness_flags=[],
    )
    risk = FinancialRiskOutput(
        debt_to_income_ratio=0.25,
        credit_score_risk_level="Good",
        loan_amount_risk="Low",
        anomaly_detection="No anomalies detected",
        reasoning="Acceptable risk.",
    )
    app = make_application()
    result = run_loan_decision_agent(app, profile, risk)
    assert "[MOCK LLM MODE" in result.explanation
    assert result.classification in ("Approved", "Rejected", "Requires Manual Review")


# ---- Test 19: Simulated notification ----
@patch("httpx.post", side_effect=_mock_post)
def test_simulated_notification(mock_http):
    from agents.compliance_action_orchestrator_agent import run_compliance_action_orchestrator_agent
    decision = LoanDecisionOutput(
        classification="Approved",
        risk_score=25.0,
        confidence_level=0.88,
        key_decision_factors=["Good credit score"],
        explanation="Meets criteria.",
    )
    result = run_compliance_action_orchestrator_agent(decision, "TEST001")
    assert isinstance(result, ComplianceActionOutput)
    assert result.notification_sent is True
    assert isinstance(result.case_id, str)
    assert isinstance(result.timestamp, datetime)
    assert isinstance(result.summary, str)


# ---- Test 20: Case ID generation ----
@patch("httpx.post", side_effect=_mock_post)
def test_case_id_generated(mock_http):
    from agents.compliance_action_orchestrator_agent import run_compliance_action_orchestrator_agent
    decision = LoanDecisionOutput(
        classification="Rejected",
        risk_score=80.0,
        confidence_level=0.92,
        key_decision_factors=["Poor credit score"],
        explanation="Does not meet criteria.",
    )
    result = run_compliance_action_orchestrator_agent(decision, "TEST002")
    assert result.case_id.startswith("CASE-")
    assert len(result.case_id) > 5
