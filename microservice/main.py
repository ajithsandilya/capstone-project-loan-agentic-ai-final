"""
FastAPI Microservice — Loan Decisioning
Receives loan applications, validates them, invokes the LangGraph orchestrator,
and returns the final result.
"""
import os
import logging
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from dotenv import load_dotenv
load_dotenv()

from microservice.schemas import (
    LoanApplicationRequest,
    LoanDecisionResponse,
    StatusResponse,
    HealthResponse,
)
from models.loan_application import LoanApplication, ApplicantProfile
from orchestration.graph import run_loan_workflow

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

MOCK_LLM_MODE = os.getenv("MOCK_LLM_MODE", "false").lower() == "true"

app = FastAPI(
    title="Loan Decisioning Microservice",
    description="Multi-Agent Agentic AI Loan Decisioning System",
    version="1.0.0",
)

# In-memory status store (proof-of-concept)
_APPLICATION_STORE: dict = {}


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok", service="loan-decisioning-microservice")


@app.post("/loan/apply", response_model=LoanDecisionResponse)
def apply_for_loan(request: LoanApplicationRequest):
    """
    Receives a loan application, validates it, runs the LangGraph workflow,
    and returns the final classified result.
    """
    # Build and validate the domain model (Pydantic validation occurs here)
    try:
        profile = ApplicantProfile(
            age=request.applicant_profile.get("age"),
            income=request.applicant_profile.get("income"),
            employment_type=request.applicant_profile.get("employment_type"),
        )
        application = LoanApplication(
            applicant_id=request.applicant_id,
            applicant_profile=profile,
            credit_score=request.credit_score,
            loan_amount=request.loan_amount,
            tenure=request.tenure,
            existing_liabilities=request.existing_liabilities,
            location=request.location,
            application_timestamp=(
                request.application_timestamp
                if request.application_timestamp
                else datetime.now(timezone.utc)
            ),
        )
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # Mark as processing
    _APPLICATION_STORE[request.applicant_id] = {"status": "processing"}

    # Run LangGraph workflow
    try:
        final_state = run_loan_workflow(application)
    except Exception as exc:
        _APPLICATION_STORE[request.applicant_id] = {"status": "error", "error": str(exc)}
        logger.error("Workflow error for %s: %s", request.applicant_id, exc)
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {exc}")

    if final_state.get("status") == "error":
        _APPLICATION_STORE[request.applicant_id] = {
            "status": "error",
            "error": final_state.get("error"),
        }
        raise HTTPException(
            status_code=500,
            detail=f"Workflow error: {final_state.get('error')}",
        )

    # Extract results
    decision = final_state["loan_decision_result"]
    compliance = final_state["compliance_action_result"]

    _APPLICATION_STORE[request.applicant_id] = {
        "status": "completed",
        "classification": decision.classification,
        "case_id": compliance.case_id,
    }

    return LoanDecisionResponse(
        applicant_id=request.applicant_id,
        classification=decision.classification,
        risk_score=decision.risk_score,
        confidence_level=decision.confidence_level,
        key_decision_factors=decision.key_decision_factors,
        explanation=decision.explanation,
        action_taken=compliance.action_taken,
        notification_sent=compliance.notification_sent,
        case_id=compliance.case_id,
        timestamp=compliance.timestamp,
        summary=compliance.summary,
        status="completed",
        mock_mode=MOCK_LLM_MODE,
    )


@app.get("/loan/status/{applicant_id}", response_model=StatusResponse)
def get_loan_status(applicant_id: str):
    """Returns the processing status of a submitted loan application."""
    record = _APPLICATION_STORE.get(applicant_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"No application found for {applicant_id}")
    return StatusResponse(
        applicant_id=applicant_id,
        status=record["status"],
        message=record.get("error") or record.get("classification") or record["status"],
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
