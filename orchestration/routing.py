"""
Decision routing for LangGraph workflow.
"""
from orchestration.state import WorkflowState


def route_after_profile(state: WorkflowState) -> str:
    """Route after Applicant Profile Agent."""
    if state.get("error"):
        return "error_handler"
    return "financial_risk_analysis"


def route_after_risk(state: WorkflowState) -> str:
    """Route after Financial Risk Analysis Agent."""
    if state.get("error"):
        return "error_handler"
    return "loan_decision"


def route_after_decision(state: WorkflowState) -> str:
    """Route after Loan Decision Agent."""
    if state.get("error"):
        return "error_handler"
    return "compliance_action"


def route_after_compliance(state: WorkflowState) -> str:
    """Route after Compliance and Action Orchestrator Agent."""
    if state.get("error"):
        return "error_handler"
    return "end"
