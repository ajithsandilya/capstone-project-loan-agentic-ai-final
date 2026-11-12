"""
Tests for MCP server endpoints via FastMCP Client.
These tests require the MCP servers to be running on their configured ports.
Run with: pytest tests/test_mcp_servers.py --run-integration
"""
import pytest
from mcp_client import call_mcp_tool_sync


pytestmark = pytest.mark.skip(reason="Requires MCP servers running. Use --run-integration to run.")


def test_applicant_db_known_applicant():
    data = call_mcp_tool_sync(
        "http://localhost:8001",
        "get_applicant_context",
        applicant_id="APP001",
        age=35,
        income=75000.0,
        employment_type="SALARIED",
    )
    assert data["applicant_id"] == "APP001"
    assert "credit_history" in data
    assert "income_stability_indicators" in data
    assert "completeness_issues" in data


def test_applicant_db_unknown_applicant_returns_default():
    data = call_mcp_tool_sync(
        "http://localhost:8001",
        "get_applicant_context",
        applicant_id="UNKNOWN999",
        age=40,
        income=60000.0,
        employment_type="CONTRACT",
    )
    assert data["applicant_id"] == "UNKNOWN999"


def test_risk_rules_db_returns_all_rules():
    data = call_mcp_tool_sync(
        "http://localhost:8002",
        "get_risk_rules",
        rule_category="all",
    )
    assert "rules" in data
    assert "disclaimer" in data
    assert "POC" in data["disclaimer"] or "PROOF" in data["disclaimer"].upper()


def test_risk_rules_db_specific_category():
    data = call_mcp_tool_sync(
        "http://localhost:8002",
        "get_risk_rules",
        rule_category="dti",
    )
    assert data["rule_category"] == "dti"


def test_decision_synthesis_produces_classification():
    data = call_mcp_tool_sync(
        "http://localhost:8003",
        "synthesize_decision",
        applicant_id="TEST001",
        credit_score=720,
        income=75000.0,
        loan_amount=150000.0,
        tenure=36,
        existing_liabilities=15000.0,
        employment_type="SALARIED",
        income_stability_score=85.0,
        employment_risk="Low",
        debt_to_income_ratio=0.20,
        credit_score_risk_level="Good",
        loan_amount_risk="Medium",
        anomaly_detection="No anomalies detected",
    )
    assert data["preliminary_classification"] in ("Approved", "Rejected", "Requires Manual Review")
    assert 0 <= data["risk_score"] <= 100
    assert 0 <= data["confidence_level"] <= 1
    assert isinstance(data["key_decision_factors"], list)


def test_notification_system_generates_case_id():
    data = call_mcp_tool_sync(
        "http://localhost:8004",
        "send_notification",
        applicant_id="TEST001",
        classification="Approved",
        risk_score=25.0,
        explanation="Good application.",
    )
    assert data["notification_sent"] is True
    assert data["case_id"].startswith("CASE-")
    assert "timestamp" in data
    assert "summary" in data


def test_notification_system_all_classifications():
    for classification in ("Approved", "Rejected", "Requires Manual Review"):
        data = call_mcp_tool_sync(
            "http://localhost:8004",
            "send_notification",
            applicant_id="TEST001",
            classification=classification,
            risk_score=50.0,
            explanation="Test.",
        )
        assert data["case_id"].startswith("CASE-")
