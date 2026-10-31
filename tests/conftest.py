"""
Shared pytest fixtures.
"""
import os
import sys
import pytest
from datetime import datetime, timezone

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Force mock LLM mode for all tests
os.environ["MOCK_LLM_MODE"] = "true"
os.environ["MCP_APPLICANT_DB_URL"] = "http://localhost:8001"
os.environ["MCP_RISK_RULES_DB_URL"] = "http://localhost:8002"
os.environ["MCP_DECISION_SYNTHESIS_URL"] = "http://localhost:8003"
os.environ["MCP_NOTIFICATION_SYSTEM_URL"] = "http://localhost:8004"


from models.loan_application import LoanApplication, ApplicantProfile


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
