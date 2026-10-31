"""
RiskRulesDB MCP Server
Provides configurable proof-of-concept risk rules for the Financial Risk Analysis Agent.
All thresholds are loaded from config/poc_rules.yaml.
"""
import os
import yaml
from pathlib import Path
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any

app = FastAPI(title="RiskRulesDB MCP Server")


def _load_rules() -> Dict[str, Any]:
    config_path = Path(__file__).parent.parent.parent / "config" / "poc_rules.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


class RiskRulesRequest(BaseModel):
    rule_category: str  # "dti", "credit_score", "loan_amount", "anomaly", "all"


class RiskRulesResponse(BaseModel):
    rule_category: str
    rules: Dict[str, Any]
    disclaimer: str


@app.get("/health")
def health():
    return {"status": "ok", "server": "RiskRulesDB"}


@app.post("/tools/get_risk_rules", response_model=RiskRulesResponse)
def get_risk_rules(req: RiskRulesRequest) -> RiskRulesResponse:
    all_rules = _load_rules()
    disclaimer = (
        "CONFIGURABLE PROOF-OF-CONCEPT RISK RULES. "
        "These thresholds are NOT real banking policy or regulatory requirements."
    )

    category_map = {
        "dti": all_rules.get("debt_to_income", {}),
        "credit_score": all_rules.get("credit_score", {}),
        "loan_amount": all_rules.get("loan_amount", {}),
        "anomaly": all_rules.get("anomaly_detection", {}),
        "income": all_rules.get("income_stability", {}),
        "employment": all_rules.get("employment_risk", {}),
        "decision": all_rules.get("decision_synthesis", {}),
    }

    if req.rule_category == "all":
        rules = category_map
    else:
        rules = {req.rule_category: category_map.get(req.rule_category, {})}

    return RiskRulesResponse(rule_category=req.rule_category, rules=rules, disclaimer=disclaimer)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("MCP_RISK_RULES_DB_PORT", "8002"))
    uvicorn.run(app, host="0.0.0.0", port=port)
