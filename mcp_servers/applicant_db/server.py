"""
ApplicantDB MCP Server
Provides contextual applicant information via in-memory mock data.
"""
import os
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any, List

app = FastAPI(title="ApplicantDB MCP Server")

# In-memory mock applicant data for proof-of-concept
MOCK_APPLICANT_RECORDS: Dict[str, Dict[str, Any]] = {
    "APP001": {
        "credit_history": "No defaults in last 5 years. Two minor late payments 3 years ago.",
        "previous_loans": 2,
        "previous_defaults": 0,
        "years_at_current_employment": 5,
        "income_verification_status": "Verified"
    },
    "APP002": {
        "credit_history": "One default recorded 2 years ago. Currently in repayment.",
        "previous_loans": 4,
        "previous_defaults": 1,
        "years_at_current_employment": 1,
        "income_verification_status": "Unverified"
    },
    "APP003": {
        "credit_history": "Excellent. No defaults, consistent repayment history over 10 years.",
        "previous_loans": 5,
        "previous_defaults": 0,
        "years_at_current_employment": 8,
        "income_verification_status": "Verified"
    },
}

DEFAULT_RECORD = {
    "credit_history": "No prior credit history on record.",
    "previous_loans": 0,
    "previous_defaults": 0,
    "years_at_current_employment": 0,
    "income_verification_status": "Unknown"
}


class ApplicantContextRequest(BaseModel):
    applicant_id: str
    age: int
    income: float
    employment_type: str


class ApplicantContextResponse(BaseModel):
    applicant_id: str
    credit_history: str
    previous_loans: int
    previous_defaults: int
    years_at_current_employment: int
    income_verification_status: str
    income_stability_indicators: List[str]
    completeness_issues: List[str]


@app.get("/health")
def health():
    return {"status": "ok", "server": "ApplicantDB"}


@app.post("/tools/get_applicant_context", response_model=ApplicantContextResponse)
def get_applicant_context(req: ApplicantContextRequest) -> ApplicantContextResponse:
    record = MOCK_APPLICANT_RECORDS.get(req.applicant_id, dict(DEFAULT_RECORD))

    # Derive income stability indicators
    indicators = []
    if req.income >= 80000:
        indicators.append("High income bracket")
    elif req.income >= 40000:
        indicators.append("Medium income bracket")
    else:
        indicators.append("Low income bracket")

    if req.employment_type.upper() in ("SALARIED", "GOVERNMENT"):
        indicators.append("Stable employment type")
    elif req.employment_type.upper() in ("SELF_EMPLOYED", "CONTRACT"):
        indicators.append("Variable employment type")
    else:
        indicators.append("High-risk employment type")

    if record["income_verification_status"] == "Verified":
        indicators.append("Income verified")
    else:
        indicators.append("Income not verified")

    # Check completeness
    completeness_issues = []
    if req.age < 18:
        completeness_issues.append("Age below minimum threshold (18)")
    if req.income <= 0:
        completeness_issues.append("Zero or negative income reported")
    if not req.employment_type.strip():
        completeness_issues.append("Employment type missing")

    return ApplicantContextResponse(
        applicant_id=req.applicant_id,
        credit_history=record["credit_history"],
        previous_loans=record["previous_loans"],
        previous_defaults=record["previous_defaults"],
        years_at_current_employment=record["years_at_current_employment"],
        income_verification_status=record["income_verification_status"],
        income_stability_indicators=indicators,
        completeness_issues=completeness_issues,
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("MCP_APPLICANT_DB_PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port)
