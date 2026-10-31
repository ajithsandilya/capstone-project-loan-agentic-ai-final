"""
Tests for the LangGraph orchestration workflow.
Tests 16 (LangGraph workflow), 17 (Claude structured output).
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


def _make_profile_output():
    return ApplicantProfileOutput(
        income_stability_score=85.0,
        employment_risk="Low",
        credit_history_summary="No defaults.",
        application_completeness_flags=[],
    )


def _make_risk_output():
    return FinancialRiskOutput(
        debt_to_income_ratio=0.20,
        credit_score_risk_level="Good",
        loan_amount_risk="Medium",
        anomaly_detection="No anomalies detected",
        reasoning="Risk is acceptable.",
    )


def _make_decision_output(classification="Approved"):
    return LoanDecisionOutput(
        classification=classification,
        risk_score=25.0,
        confidence_level=0.88,
        key_decision_factors=["Good credit score"],
        explanation="Application meets criteria.",
    )


def _make_compliance_output():
    return ComplianceActionOutput(
        action_taken="Loan approval letter prepared.",
        notification_sent=True,
        case_id="CASE-ABCD1234",
        timestamp=datetime.now(timezone.utc),
        summary="Application TEST001 APPROVED.",
    )


# ---- Test 16: LangGraph workflow execution ----
@patch("orchestration.graph.run_applicant_profile_agent", return_value=_make_profile_output())
@patch("orchestration.graph.run_financial_risk_analysis_agent", return_value=_make_risk_output())
@patch("orchestration.graph.run_loan_decision_agent", return_value=_make_decision_output())
@patch("orchestration.graph.run_compliance_action_orchestrator_agent", return_value=_make_compliance_output())
def test_langgraph_workflow_executes(mock_compliance, mock_decision, mock_risk, mock_profile):
    from orchestration.graph import run_loan_workflow
    app = make_application()
    state = run_loan_workflow(app)
    assert state["status"] == "completed"
    assert state["final_decision"] in ("Approved", "Rejected", "Requires Manual Review")
    assert state["applicant_profile_result"] is not None
    assert state["financial_risk_result"] is not None
    assert state["loan_decision_result"] is not None
    assert state["compliance_action_result"] is not None


@patch("orchestration.graph.run_applicant_profile_agent", return_value=_make_profile_output())
@patch("orchestration.graph.run_financial_risk_analysis_agent", return_value=_make_risk_output())
@patch("orchestration.graph.run_loan_decision_agent", return_value=_make_decision_output())
@patch("orchestration.graph.run_compliance_action_orchestrator_agent", return_value=_make_compliance_output())
def test_workflow_invokes_all_four_agents(mock_compliance, mock_decision, mock_risk, mock_profile):
    from orchestration.graph import run_loan_workflow
    app = make_application()
    run_loan_workflow(app)
    mock_profile.assert_called_once()
    mock_risk.assert_called_once()
    mock_decision.assert_called_once()
    mock_compliance.assert_called_once()


# ---- Test 17: Claude structured-output handling (mock mode) ----
def test_mock_llm_output_matches_schema():
    from agents.loan_decision_agent import _mock_decision
    synthesis = {
        "risk_score": 30.0,
        "confidence_level": 0.85,
        "preliminary_classification": "Approved",
        "key_decision_factors": ["Good credit"],
        "synthesis_context": "context",
    }
    result = _mock_decision(synthesis)
    assert result["classification"] in ("Approved", "Rejected", "Requires Manual Review")
    assert 0 <= result["risk_score"] <= 100
    assert 0 <= result["confidence_level"] <= 1
    assert isinstance(result["key_decision_factors"], list)
    assert isinstance(result["explanation"], str)
    assert "[MOCK LLM MODE" in result["explanation"]


def test_classification_normalization():
    from agents.loan_decision_agent import _normalize_classification
    assert _normalize_classification("Approved") == "Approved"
    assert _normalize_classification("approved") == "Approved"
    assert _normalize_classification("Approve") == "Approved"
    assert _normalize_classification("Rejected") == "Rejected"
    assert _normalize_classification("reject") == "Rejected"
    assert _normalize_classification("Requires Manual Review") == "Requires Manual Review"
    assert _normalize_classification("Review") == "Requires Manual Review"
    assert _normalize_classification("Pending") == "Requires Manual Review"
    assert _normalize_classification("Escalated") == "Requires Manual Review"
    assert _normalize_classification("Conditional Approval") == "Requires Manual Review"
