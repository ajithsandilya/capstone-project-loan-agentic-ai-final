"""
Financial Risk Analysis Agent
MCP Server: RiskRulesDB
Performs financial risk analysis using configurable proof-of-concept rules.
"""
import os
import httpx
from models.loan_application import LoanApplication
from models.agent_outputs import FinancialRiskOutput


MCP_RISK_RULES_DB_URL = os.getenv("MCP_RISK_RULES_DB_URL", "http://localhost:8002")


def run_financial_risk_analysis_agent(application: LoanApplication) -> FinancialRiskOutput:
    """
    Fetches risk rules from RiskRulesDB MCP server and performs financial risk analysis.
    """
    profile = application.applicant_profile

    # Fetch all configurable rules from RiskRulesDB
    response = httpx.post(
        f"{MCP_RISK_RULES_DB_URL}/tools/get_risk_rules",
        json={"rule_category": "all"},
        timeout=10.0,
    )
    response.raise_for_status()
    rules_payload = response.json()
    rules = rules_payload.get("rules", {})

    dti_rules = rules.get("dti", {})
    cs_rules = rules.get("credit_score", {})
    la_rules = rules.get("loan_amount", {})
    anomaly_rules = rules.get("anomaly", {})

    # ---- Debt-to-Income Ratio ----
    if profile.income <= 0:
        dti = 0.0
        dti_reasoning = "Income is zero; DTI ratio cannot be calculated. High risk assumed."
        is_zero_income = True
    else:
        dti = application.existing_liabilities / profile.income
        is_zero_income = False
        dti_reasoning = f"DTI = {application.existing_liabilities} / {profile.income} = {dti:.4f}"

    # ---- Credit Score Risk Level ----
    cs = application.credit_score
    excellent_min = cs_rules.get("excellent_min", 750)
    good_min = cs_rules.get("good_min", 650)
    fair_min = cs_rules.get("fair_min", 550)

    if cs >= excellent_min:
        credit_score_risk_level = "Excellent"
    elif cs >= good_min:
        credit_score_risk_level = "Good"
    elif cs >= fair_min:
        credit_score_risk_level = "Fair"
    else:
        credit_score_risk_level = "Poor"

    # ---- Loan Amount Risk ----
    la = application.loan_amount
    la_low_max = la_rules.get("low_risk_max", 100000)
    la_med_max = la_rules.get("medium_risk_max", 500000)

    if la <= la_low_max:
        loan_amount_risk = "Low"
    elif la <= la_med_max:
        loan_amount_risk = "Medium"
    else:
        loan_amount_risk = "High"

    # ---- Anomaly Detection ----
    anomaly_flags = []
    age_min = anomaly_rules.get("age_min", 18)
    age_max = anomaly_rules.get("age_max", 75)
    loan_to_income_max = anomaly_rules.get("loan_to_income_ratio_max", 10.0)
    tenure_min = anomaly_rules.get("tenure_min", 6)

    if profile.age < age_min or profile.age > age_max:
        anomaly_flags.append(f"Applicant age {profile.age} outside normal range ({age_min}–{age_max})")

    if profile.income > 0:
        lti = application.loan_amount / profile.income
        if lti > loan_to_income_max:
            anomaly_flags.append(
                f"Loan-to-income ratio {lti:.1f}x exceeds threshold ({loan_to_income_max}x)"
            )
    elif is_zero_income:
        anomaly_flags.append("Zero income is anomalous for a loan application")

    if application.tenure < tenure_min:
        anomaly_flags.append(f"Tenure {application.tenure} months below minimum ({tenure_min} months)")

    if not is_zero_income and dti > 0.80:
        anomaly_flags.append(f"Extremely high DTI ratio ({dti:.2f}) flagged as anomalous")

    anomaly_detection = "; ".join(anomaly_flags) if anomaly_flags else "No anomalies detected"

    # ---- Reasoning ----
    low_max = dti_rules.get("low_risk_max", 0.30)
    med_max = dti_rules.get("medium_risk_max", 0.50)

    if is_zero_income:
        dti_band = "High (zero income)"
    elif dti <= low_max:
        dti_band = "Low"
    elif dti <= med_max:
        dti_band = "Medium"
    else:
        dti_band = "High"

    reasoning_parts = [
        f"Credit score {cs} classified as '{credit_score_risk_level}'.",
        f"DTI ratio {dti:.2f} is '{dti_band}' ({dti_reasoning}).",
        f"Loan amount {application.loan_amount} classified as '{loan_amount_risk}' risk.",
    ]
    if anomaly_flags:
        reasoning_parts.append(f"Anomalies: {anomaly_detection}.")
    else:
        reasoning_parts.append("No anomalies detected.")

    reasoning = " ".join(reasoning_parts)

    return FinancialRiskOutput(
        debt_to_income_ratio=round(dti, 4),
        credit_score_risk_level=credit_score_risk_level,
        loan_amount_risk=loan_amount_risk,
        anomaly_detection=anomaly_detection,
        reasoning=reasoning,
    )
