"""
Applicant Profile Agent
MCP Server: ApplicantDB
Analyzes applicant profile and produces structured output.
"""
import os
import httpx
from models.loan_application import LoanApplication
from models.agent_outputs import ApplicantProfileOutput


MCP_APPLICANT_DB_URL = os.getenv("MCP_APPLICANT_DB_URL", "http://localhost:8001")


def run_applicant_profile_agent(application: LoanApplication) -> ApplicantProfileOutput:
    """
    Calls ApplicantDB MCP server to get contextual data,
    then analyses the applicant profile.
    """
    profile = application.applicant_profile

    # Call ApplicantDB MCP server
    response = httpx.post(
        f"{MCP_APPLICANT_DB_URL}/tools/get_applicant_context",
        json={
            "applicant_id": application.applicant_id,
            "age": profile.age,
            "income": profile.income,
            "employment_type": profile.employment_type,
        },
        timeout=10.0,
    )
    response.raise_for_status()
    ctx = response.json()

    # Derive Income Stability Score (0–100)
    income_stability_score = _calculate_income_stability(
        income=profile.income,
        employment_type=profile.employment_type,
        income_verified=(ctx.get("income_verification_status") == "Verified"),
    )

    # Derive Employment Risk
    employment_risk = _classify_employment_risk(profile.employment_type)

    # Credit History Summary
    defaults = ctx.get("previous_defaults", 0)
    previous_loans = ctx.get("previous_loans", 0)
    credit_history = ctx.get("credit_history", "No credit history available.")
    credit_summary = (
        f"{credit_history} "
        f"Previous loans: {previous_loans}. Defaults: {defaults}."
    )

    # Application Completeness Flags (from MCP + local validation)
    flags = list(ctx.get("completeness_issues", []))
    if application.loan_amount <= 0:
        flags.append("Loan amount must be greater than zero")
    if application.tenure < 1:
        flags.append("Tenure must be at least 1 month")

    return ApplicantProfileOutput(
        income_stability_score=income_stability_score,
        employment_risk=employment_risk,
        credit_history_summary=credit_summary,
        application_completeness_flags=flags,
    )


def _calculate_income_stability(income: float, employment_type: str, income_verified: bool) -> float:
    """Derives income stability score 0–100 from income, employment type, and verification."""
    base = 0.0
    # Income bracket contribution (up to 50 points)
    if income >= 80000:
        base += 50.0
    elif income >= 40000:
        base += 30.0
    elif income > 0:
        base += 15.0
    # else zero income: 0 points

    # Employment type contribution (up to 35 points)
    emp = employment_type.upper()
    if emp in ("SALARIED", "GOVERNMENT"):
        base += 35.0
    elif emp in ("SELF_EMPLOYED", "CONTRACT"):
        base += 20.0
    elif emp in ("PART_TIME",):
        base += 10.0
    # UNEMPLOYED / OTHER: 0

    # Verification bonus (up to 15 points)
    if income_verified:
        base += 15.0

    return round(min(base, 100.0), 1)


def _classify_employment_risk(employment_type: str) -> str:
    emp = employment_type.upper()
    if emp in ("SALARIED", "GOVERNMENT"):
        return "Low"
    elif emp in ("SELF_EMPLOYED", "CONTRACT"):
        return "Medium"
    else:
        return "High"
