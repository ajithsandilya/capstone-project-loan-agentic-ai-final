"""
Tests for MCP server endpoints.
"""
import pytest
from fastapi.testclient import TestClient


# ---- ApplicantDB ----
def test_applicant_db_health():
    from mcp_servers.applicant_db.server import app
    c = TestClient(app)
    r = c.get("/health")
    assert r.status_code == 200
    assert r.json()["server"] == "ApplicantDB"


def test_applicant_db_known_applicant():
    from mcp_servers.applicant_db.server import app
    c = TestClient(app)
    r = c.post("/tools/get_applicant_context", json={
        "applicant_id": "APP001",
        "age": 35,
        "income": 75000.0,
        "employment_type": "SALARIED",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["applicant_id"] == "APP001"
    assert "credit_history" in data
    assert "income_stability_indicators" in data
    assert "completeness_issues" in data


def test_applicant_db_unknown_applicant_returns_default():
    from mcp_servers.applicant_db.server import app
    c = TestClient(app)
    r = c.post("/tools/get_applicant_context", json={
        "applicant_id": "UNKNOWN999",
        "age": 40,
        "income": 60000.0,
        "employment_type": "CONTRACT",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["applicant_id"] == "UNKNOWN999"


# ---- Test 15: MCP server response handling ----
def test_risk_rules_db_returns_all_rules():
    from mcp_servers.risk_rules_db.server import app
    c = TestClient(app)
    r = c.post("/tools/get_risk_rules", json={"rule_category": "all"})
    assert r.status_code == 200
    data = r.json()
    assert "rules" in data
    assert "disclaimer" in data
    assert "POC" in data["disclaimer"] or "PROOF" in data["disclaimer"].upper()


def test_risk_rules_db_specific_category():
    from mcp_servers.risk_rules_db.server import app
    c = TestClient(app)
    r = c.post("/tools/get_risk_rules", json={"rule_category": "dti"})
    assert r.status_code == 200
    data = r.json()
    assert data["rule_category"] == "dti"


def test_decision_synthesis_produces_classification():
    from mcp_servers.decision_synthesis.server import app
    c = TestClient(app)
    r = c.post("/tools/synthesize_decision", json={
        "applicant_id": "TEST001",
        "credit_score": 720,
        "income": 75000.0,
        "loan_amount": 150000.0,
        "tenure": 36,
        "existing_liabilities": 15000.0,
        "employment_type": "SALARIED",
        "income_stability_score": 85.0,
        "employment_risk": "Low",
        "debt_to_income_ratio": 0.20,
        "credit_score_risk_level": "Good",
        "loan_amount_risk": "Medium",
        "anomaly_detection": "No anomalies detected",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["preliminary_classification"] in ("Approved", "Rejected", "Requires Manual Review")
    assert 0 <= data["risk_score"] <= 100
    assert 0 <= data["confidence_level"] <= 1
    assert isinstance(data["key_decision_factors"], list)


def test_notification_system_generates_case_id():
    from mcp_servers.notification_system.server import app
    c = TestClient(app)
    r = c.post("/tools/send_notification", json={
        "applicant_id": "TEST001",
        "classification": "Approved",
        "risk_score": 25.0,
        "explanation": "Good application.",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["notification_sent"] is True
    assert data["case_id"].startswith("CASE-")
    assert "timestamp" in data
    assert "summary" in data


def test_notification_system_all_classifications():
    from mcp_servers.notification_system.server import app
    c = TestClient(app)
    for classification in ("Approved", "Rejected", "Requires Manual Review"):
        r = c.post("/tools/send_notification", json={
            "applicant_id": "TEST001",
            "classification": classification,
            "risk_score": 50.0,
            "explanation": "Test.",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["case_id"].startswith("CASE-")
