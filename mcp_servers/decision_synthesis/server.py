"""
DecisionSynthesis MCP Server
Supports the Loan Decision Agent in combining agent outputs into a decision context.
"""
import os
import yaml
from pathlib import Path
from fastmcp import FastMCP
from pydantic import BaseModel
from typing import Dict, Any, List, Literal

mcp = FastMCP("DecisionSynthesis MCP Server")


def _load_rules() -> Dict[str, Any]:
    config_path = Path(__file__).parent.parent.parent / "config" / "poc_rules.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


class SynthesisRequest(BaseModel):
    applicant_id: str
    credit_score: int
    income: float
    loan_amount: float
    tenure: int
    existing_liabilities: float
    employment_type: str
    income_stability_score: float
    employment_risk: str
    debt_to_income_ratio: float
    credit_score_risk_level: str
    loan_amount_risk: str
    anomaly_detection: str


class SynthesisResponse(BaseModel):
    risk_score: float
    confidence_level: float
    preliminary_classification: Literal["Approved", "Rejected", "Requires Manual Review"]
    key_decision_factors: List[str]
    synthesis_context: str


@mcp.tool()
def synthesize_decision(
    applicant_id: str,
    credit_score: int,
    income: float,
    loan_amount: float,
    tenure: int,
    existing_liabilities: float,
    employment_type: str,
    income_stability_score: float,
    employment_risk: str,
    debt_to_income_ratio: float,
    credit_score_risk_level: str,
    loan_amount_risk: str,
    anomaly_detection: str,
) -> Dict[str, Any]:
    rules = _load_rules()
    ds_rules = rules.get("decision_synthesis", {})
    cs_rules = rules.get("credit_score", {})
    dti_rules = rules.get("debt_to_income", {})
    la_rules = rules.get("loan_amount", {})

    # ---- Credit score component (0–100, lower = riskier) ----
    cs = credit_score
    if cs >= cs_rules.get("excellent_min", 750):
        cs_component = 10.0
    elif cs >= cs_rules.get("good_min", 650):
        cs_component = 30.0
    elif cs >= cs_rules.get("fair_min", 550):
        cs_component = 60.0
    else:
        cs_component = 85.0

    # ---- DTI component ----
    dti = debt_to_income_ratio
    if dti <= dti_rules.get("low_risk_max", 0.30):
        dti_component = 10.0
    elif dti <= dti_rules.get("medium_risk_max", 0.50):
        dti_component = 45.0
    else:
        dti_component = 80.0

    # ---- Loan amount component ----
    la = loan_amount
    if la <= la_rules.get("low_risk_max", 100000):
        la_component = 10.0
    elif la <= la_rules.get("medium_risk_max", 500000):
        la_component = 40.0
    else:
        la_component = 75.0

    # ---- Employment component ----
    emp = employment_risk.lower()
    if emp == "low":
        emp_component = 10.0
    elif emp == "medium":
        emp_component = 40.0
    else:
        emp_component = 80.0

    # ---- Weighted risk score ----
    w_cs = ds_rules.get("credit_score_weight", 0.35)
    w_dti = ds_rules.get("dti_weight", 0.30)
    w_la = ds_rules.get("loan_amount_weight", 0.20)
    w_emp = ds_rules.get("employment_weight", 0.15)

    risk_score = (
        cs_component * w_cs +
        dti_component * w_dti +
        la_component * w_la +
        emp_component * w_emp
    )

    # ---- Confidence (agreement between components) ----
    components = [cs_component, dti_component, la_component, emp_component]
    spread = max(components) - min(components)
    if spread < 20:
        confidence = 0.90
    elif spread < 45:
        confidence = 0.70
    else:
        confidence = 0.55

    # Anomaly detected lowers confidence
    if "anomaly" in anomaly_detection.lower() and "no anomal" not in anomaly_detection.lower():
        confidence = max(0.40, confidence - 0.15)
        risk_score = min(100, risk_score + 10)

    # ---- Classification ----
    approved_max = ds_rules.get("approved_max_risk", 35)
    manual_max = ds_rules.get("manual_review_max_risk", 65)

    if risk_score <= approved_max:
        classification: Literal["Approved", "Rejected", "Requires Manual Review"] = "Approved"
    elif risk_score <= manual_max:
        classification = "Requires Manual Review"
    else:
        classification = "Rejected"

    # ---- Key factors ----
    factors = []
    if cs_component >= 60:
        factors.append(f"Credit score {credit_score} indicates elevated risk")
    else:
        factors.append(f"Credit score {credit_score} is within acceptable range")

    if dti_component >= 45:
        factors.append(f"Debt-to-income ratio {debt_to_income_ratio:.2f} is elevated")
    else:
        factors.append(f"Debt-to-income ratio {debt_to_income_ratio:.2f} is acceptable")

    if la_component >= 40:
        factors.append(f"Loan amount {loan_amount} presents medium-to-high risk")
    if emp_component >= 40:
        factors.append(f"Employment type '{employment_type}' carries elevated risk")
    if "anomaly" in anomaly_detection.lower() and "no anomal" not in anomaly_detection.lower():
        factors.append(f"Anomaly detected: {anomaly_detection}")

    context = (
        f"Risk Score: {risk_score:.1f}/100 | "
        f"Confidence: {confidence:.0%} | "
        f"Credit Score Risk: {credit_score_risk_level} | "
        f"DTI: {debt_to_income_ratio:.2f} | "
        f"Loan Amount Risk: {loan_amount_risk} | "
        f"Employment Risk: {employment_risk}"
    )

    return {
        "risk_score": round(risk_score, 1),
        "confidence_level": round(confidence, 2),
        "preliminary_classification": classification,
        "key_decision_factors": factors,
        "synthesis_context": context,
    }


app = mcp.http_app()


if __name__ == "__main__":
    port = int(os.getenv("MCP_DECISION_SYNTHESIS_PORT", "8003"))
    mcp.run(transport="http", host="0.0.0.0", port=port)
