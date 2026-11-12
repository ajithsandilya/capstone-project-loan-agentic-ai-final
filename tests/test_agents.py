"""
Tests for the four agents and their output schemas.
Uses mock HTTP calls to MCP servers (mocked via conftest fixture).
"""
import pytest
from datetime import datetime, timezone

from models.loan_application import LoanApplication, ApplicantProfile
from models.agent_outputs import (
    ApplicantProfileOutput,
    FinancialRiskOutput,
    LoanDecisionOutput,
    ComplianceActionOutput,
)
from tests.conftest import make_application


# ---- Test: Applicant Profile Agent output ----
def test_applicant_profile_agent_output():
    from agents.applicant_profile_agent import run_applicant_profile_agent
    app = make_application()
    result = run_applicant_profile_agent(app)
    assert isinstance(result, ApplicantProfileOutput)
    assert 0 <= result.income_stability_score <= 100
    assert result.employment_risk in ("Low", "Medium", "High")
    assert isinstance(result.credit_history_summary, str)
    assert isinstance(result.application_completeness_flags, list)


# ---- Test: Financial Risk Analysis Agent output ----
def test_financial_risk_analysis_agent_output():
    from agents.financial_risk_analysis_agent import run_financial_risk_analysis_agent
    app = make_application()
    result = run_financial_risk_analysis_agent(app)
    assert isinstance(result, FinancialRiskOutput)
    assert result.debt_to_income_ratio >= 0
    assert result.credit_score_risk_level in ("Excellent", "Good", "Fair", "Poor")
    assert result.loan_amount_risk in ("Low", "Medium", "High")
    assert isinstance(result.anomaly_detection, str)
    assert isinstance(result.reasoning, str)


# ---- Test: Debt-to-Income Ratio calculation ----
def test_dti_ratio_calculation():
    from agents.financial_risk_analysis_agent import run_financial_risk_analysis_agent
    app = make_application(
        applicant_profile=ApplicantProfile(age=35, income=50000.0, employment_type="SALARIED"),
        existing_liabilities=15000.0,
    )
    result = run_financial_risk_analysis_agent(app)
    expected_dti = 15000.0 / 50000.0
    assert abs(result.debt_to_income_ratio - expected_dti) < 0.001


# ---- Test: Zero-income handling ----
def test_zero_income_handling():
    from agents.financial_risk_analysis_agent import run_financial_risk_analysis_agent
    app = make_application(
        applicant_profile=ApplicantProfile(age=35, income=0.0, employment_type="UNEMPLOYED"),
        existing_liabilities=5000.0,
    )
    result = run_financial_risk_analysis_agent(app)
    assert result.debt_to_income_ratio == 0.0
    assert "zero" in result.reasoning.lower() or "income" in result.reasoning.lower()


# ---- Test: Approved classification (mock LLM) ----
def test_loan_decision_approved():
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


# ---- Test: Classification normalization ----
def test_loan_decision_classification_normalization():
    from agents.loan_decision_agent import _normalize_classification

    assert _normalize_classification("Approved") == "Approved"
    assert _normalize_classification("APPROVED") == "Approved"
    assert _normalize_classification("approve") == "Approved"
    assert _normalize_classification("Rejected") == "Rejected"
    assert _normalize_classification("reject") == "Rejected"
    assert _normalize_classification("Requires Manual Review") == "Requires Manual Review"
    assert _normalize_classification("manual review") == "Requires Manual Review"
    assert _normalize_classification("ambiguous") == "Requires Manual Review"


# ---- Test: Mock LLM mode ----
def test_mock_llm_mode_produces_valid_output():
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


# ---- Test: Simulated notification ----
def test_simulated_notification():
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


# ---- Test: Case ID generation ----
def test_case_id_generated():
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
