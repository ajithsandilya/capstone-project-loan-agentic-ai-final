from pydantic import BaseModel, Field
from typing import Literal, List
from datetime import datetime


# ------- Applicant Profile Agent Output -------
class ApplicantProfileOutput(BaseModel):
    income_stability_score: float = Field(..., description="Score 0-100 reflecting income stability")
    employment_risk: Literal["Low", "Medium", "High"] = Field(..., description="Employment risk level")
    credit_history_summary: str = Field(..., description="Narrative summary of credit history")
    application_completeness_flags: List[str] = Field(
        default_factory=list,
        description="List of missing or flagged fields; empty means complete"
    )


# ------- Financial Risk Analysis Agent Output -------
class FinancialRiskOutput(BaseModel):
    debt_to_income_ratio: float = Field(..., description="DTI ratio (liabilities / income)")
    credit_score_risk_level: Literal["Excellent", "Good", "Fair", "Poor"] = Field(
        ..., description="Credit score risk band"
    )
    loan_amount_risk: Literal["Low", "Medium", "High"] = Field(..., description="Loan amount risk level")
    anomaly_detection: str = Field(..., description="Anomaly flags or 'No anomalies detected'")
    reasoning: str = Field(..., description="Explanation of the financial risk assessment")


# ------- Loan Decision Agent Output -------
class LoanDecisionOutput(BaseModel):
    classification: Literal["Approved", "Rejected", "Requires Manual Review"] = Field(
        ..., description="Final loan classification"
    )
    risk_score: float = Field(..., ge=0, le=100, description="Composite risk score 0-100")
    confidence_level: float = Field(..., ge=0, le=1, description="Confidence in the decision (0-1)")
    key_decision_factors: List[str] = Field(..., description="Primary factors driving the decision")
    explanation: str = Field(..., description="Concise explanation of the decision")


# ------- Compliance and Action Orchestrator Agent Output -------
class ComplianceActionOutput(BaseModel):
    action_taken: str = Field(..., description="Action performed based on the decision")
    notification_sent: bool = Field(..., description="Whether notification was simulated")
    case_id: str = Field(..., description="Unique case identifier")
    timestamp: datetime = Field(..., description="UTC timestamp of action")
    summary: str = Field(..., description="Summary corresponding to the classification")
