"""
Shared pytest fixtures.
"""
import os
import sys
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Force mock LLM mode for all tests
os.environ["MOCK_LLM_MODE"] = "true"
os.environ["MCP_APPLICANT_DB_URL"] = "http://localhost:8001"
os.environ["MCP_RISK_RULES_DB_URL"] = "http://localhost:8002"
os.environ["MCP_DECISION_SYNTHESIS_URL"] = "http://localhost:8003"
os.environ["MCP_NOTIFICATION_SYSTEM_URL"] = "http://localhost:8004"


from models.loan_application import LoanApplication, ApplicantProfile
from mcp_client import set_mcp_post_override


def make_application(**overrides) -> LoanApplication:
    defaults = dict(
        applicant_id="TEST001",
        applicant_profile=ApplicantProfile(age=35, income=75000.0, employment_type="SALARIED"),
        credit_score=720,
        loan_amount=150000.0,
        tenure=36,
        existing_liabilities=15000.0,
        location="New York",
        application_timestamp=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    return LoanApplication(**defaults)


@pytest.fixture
def good_application():
    return make_application()


@pytest.fixture
def high_risk_application():
    return make_application(
        applicant_id="TEST_HIGH_RISK",
        applicant_profile=ApplicantProfile(age=28, income=20000.0, employment_type="UNEMPLOYED"),
        credit_score=380,
        loan_amount=800000.0,
        tenure=12,
        existing_liabilities=18000.0,
    )


@pytest.fixture
def borderline_application():
    return make_application(
        applicant_id="TEST_BORDERLINE",
        applicant_profile=ApplicantProfile(age=42, income=55000.0, employment_type="SELF_EMPLOYED"),
        credit_score=610,
        loan_amount=200000.0,
        tenure=60,
        existing_liabilities=20000.0,
    )


@pytest.fixture(autouse=True)
def mock_mcp_calls():
    """Auto-use fixture to mock all MCP HTTP calls."""
    from datetime import datetime, timezone

    # Mock response data
    mock_applicant_ctx = {
        "applicant_id": "TEST001",
        "credit_history": "No defaults.",
        "previous_loans": 2,
        "previous_defaults": 0,
        "years_at_current_employment": 5,
        "income_verification_status": "Verified",
        "income_stability_indicators": ["High income bracket", "Stable employment type"],
        "completeness_issues": [],
    }

    mock_risk_rules = {
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

    mock_synthesis = {
        "risk_score": 25.0,
        "confidence_level": 0.88,
        "preliminary_classification": "Approved",
        "key_decision_factors": ["Good credit score"],
        "synthesis_context": "Risk Score: 25.0/100",
    }

    mock_notification = {
        "action_taken": "Loan approval letter prepared.",
        "notification_sent": True,
        "case_id": "CASE-ABCD1234",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": "Application TEST001 APPROVED.",
    }

    def mock_post(url, json=None, timeout=None):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        if "get_applicant_context" in url:
            mock_resp.json.return_value = mock_applicant_ctx
        elif "get_risk_rules" in url:
            mock_resp.json.return_value = mock_risk_rules
        elif "synthesize_decision" in url:
            mock_resp.json.return_value = mock_synthesis
        elif "send_notification" in url:
            mock_resp.json.return_value = mock_notification
        return mock_resp

    set_mcp_post_override(mock_post)
    yield
    set_mcp_post_override(None)
