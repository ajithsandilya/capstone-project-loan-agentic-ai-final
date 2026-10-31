"""
LangGraph workflow state definition.
Contains only the information required to execute the stated workflow.
"""
from typing import Optional, TypedDict
from models.loan_application import LoanApplication
from models.agent_outputs import (
    ApplicantProfileOutput,
    FinancialRiskOutput,
    LoanDecisionOutput,
    ComplianceActionOutput,
)


class WorkflowState(TypedDict, total=False):
    # Input
    loan_application: LoanApplication

    # Agent results
    applicant_profile_result: Optional[ApplicantProfileOutput]
    financial_risk_result: Optional[FinancialRiskOutput]
    loan_decision_result: Optional[LoanDecisionOutput]
    compliance_action_result: Optional[ComplianceActionOutput]

    # Final decision (mirrors loan_decision_result.classification)
    final_decision: Optional[str]

    # Processing status
    status: str  # "pending" | "processing" | "completed" | "error"

    # Error information
    error: Optional[str]
