"""
FastAPI request/response schemas.
Technical envelopes only — business models live in models/.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime


class LoanApplicationRequest(BaseModel):
    applicant_id: str
    applicant_profile: dict = Field(..., description="Must contain age, income, employment_type")
    credit_score: int
    loan_amount: float
    tenure: int
    existing_liabilities: float
    location: str
    application_timestamp: Optional[datetime] = None


class LoanDecisionResponse(BaseModel):
    applicant_id: str
    classification: Literal["Approved", "Rejected", "Requires Manual Review"]
    risk_score: float
    confidence_level: float
    key_decision_factors: List[str]
    explanation: str
    action_taken: str
    notification_sent: bool
    case_id: str
    timestamp: datetime
    summary: str
    status: str
    mock_mode: bool


class StatusResponse(BaseModel):
    applicant_id: str
    status: str
    message: str


class HealthResponse(BaseModel):
    status: str
    service: str
