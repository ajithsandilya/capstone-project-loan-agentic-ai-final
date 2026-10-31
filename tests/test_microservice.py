"""
Tests for the FastAPI microservice validation layer.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from microservice.main import app
from models.agent_outputs import (
    LoanDecisionOutput, ComplianceActionOutput, ApplicantProfileOutput, FinancialRiskOutput
)

client = TestClient(app)

VALID_PAYLOAD = {
    "applicant_id": "APP001",
    "applicant_profile": {"age": 35, "income": 75000.0, "employment_type": "SALARIED"},
    "credit_score": 720,
    "loan_amount": 150000.0,
    "tenure": 36,
    "existing_liabilities": 15000.0,
    "location": "New York",
}


def _mock_workflow(application):
    decision = LoanDecisionOutput(
        classification="Approved",
        risk_score=25.0,
        confidence_level=0.88,
        key_decision_factors=["Good credit score"],
        explanation="Application meets criteria.",
    )
    compliance = ComplianceActionOutput(
        action_taken="Loan approval letter prepared.",
        notification_sent=True,
        case_id="CASE-ABCD1234",
        timestamp=datetime.now(timezone.utc),
        summary="Application APP001 APPROVED.",
    )
    return {
        "status": "completed",
        "loan_decision_result": decision,
        "compliance_action_result": compliance,
        "final_decision": "Approved",
        "error": None,
    }


# ---- Health check ----
def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ---- Test 1: Valid loan application submission ----
@patch("microservice.main.run_loan_workflow", side_effect=_mock_workflow)
def test_valid_application_submission(mock_wf):
    r = client.post("/loan/apply", json=VALID_PAYLOAD)
    assert r.status_code == 200
    data = r.json()
    assert data["classification"] in ("Approved", "Rejected", "Requires Manual Review")
    assert "case_id" in data
    assert "risk_score" in data


# ---- Test 2: Missing required input (applicant_id empty) ----
def test_missing_applicant_id():
    payload = {**VALID_PAYLOAD, "applicant_id": "   "}
    r = client.post("/loan/apply", json=payload)
    assert r.status_code == 422


# ---- Test 3: Invalid applicant age (below 18) ----
def test_invalid_age_below_minimum():
    payload = {**VALID_PAYLOAD, "applicant_profile": {"age": 15, "income": 50000.0, "employment_type": "SALARIED"}}
    r = client.post("/loan/apply", json=payload)
    assert r.status_code == 422


# ---- Test 4: Invalid income (negative) ----
def test_invalid_income_negative():
    payload = {**VALID_PAYLOAD, "applicant_profile": {"age": 30, "income": -1000.0, "employment_type": "SALARIED"}}
    r = client.post("/loan/apply", json=payload)
    assert r.status_code == 422


# ---- Test 5: Invalid credit score (below 300) ----
def test_invalid_credit_score_low():
    payload = {**VALID_PAYLOAD, "credit_score": 200}
    r = client.post("/loan/apply", json=payload)
    assert r.status_code == 422


# ---- Test 6: Invalid loan amount (zero) ----
def test_invalid_loan_amount_zero():
    payload = {**VALID_PAYLOAD, "loan_amount": 0}
    r = client.post("/loan/apply", json=payload)
    assert r.status_code == 422


# ---- Test 7: Invalid tenure (zero) ----
def test_invalid_tenure_zero():
    payload = {**VALID_PAYLOAD, "tenure": 0}
    r = client.post("/loan/apply", json=payload)
    assert r.status_code == 422


# ---- Test 21: Final result returned through FastAPI ----
@patch("microservice.main.run_loan_workflow", side_effect=_mock_workflow)
def test_final_result_returned(mock_wf):
    r = client.post("/loan/apply", json=VALID_PAYLOAD)
    assert r.status_code == 200
    data = r.json()
    required_fields = [
        "applicant_id", "classification", "risk_score", "confidence_level",
        "key_decision_factors", "explanation", "action_taken",
        "notification_sent", "case_id", "timestamp", "summary",
    ]
    for field in required_fields:
        assert field in data, f"Missing field: {field}"
