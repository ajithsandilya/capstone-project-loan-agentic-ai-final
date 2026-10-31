"""
LangGraph orchestration engine.
Coordinates the four-agent workflow for loan decisioning.
"""
import logging
from langgraph.graph import StateGraph, END

from orchestration.state import WorkflowState
from orchestration.routing import (
    route_after_profile,
    route_after_risk,
    route_after_decision,
    route_after_compliance,
)
from agents.applicant_profile_agent import run_applicant_profile_agent
from agents.financial_risk_analysis_agent import run_financial_risk_analysis_agent
from agents.loan_decision_agent import run_loan_decision_agent
from agents.compliance_action_orchestrator_agent import run_compliance_action_orchestrator_agent
from models.loan_application import LoanApplication

logger = logging.getLogger(__name__)


# ---- Node implementations ----

def node_applicant_profile(state: WorkflowState) -> WorkflowState:
    logger.info("Invoking Applicant Profile Agent")
    try:
        application: LoanApplication = state["loan_application"]
        result = run_applicant_profile_agent(application)
        return {**state, "applicant_profile_result": result, "status": "processing"}
    except Exception as exc:
        logger.error("Applicant Profile Agent failed: %s", exc)
        return {**state, "error": f"Applicant Profile Agent error: {exc}", "status": "error"}


def node_financial_risk(state: WorkflowState) -> WorkflowState:
    logger.info("Invoking Financial Risk Analysis Agent")
    try:
        application: LoanApplication = state["loan_application"]
        result = run_financial_risk_analysis_agent(application)
        return {**state, "financial_risk_result": result}
    except Exception as exc:
        logger.error("Financial Risk Analysis Agent failed: %s", exc)
        return {**state, "error": f"Financial Risk Analysis Agent error: {exc}", "status": "error"}


def node_loan_decision(state: WorkflowState) -> WorkflowState:
    logger.info("Invoking Loan Decision Agent")
    try:
        application: LoanApplication = state["loan_application"]
        profile_output = state["applicant_profile_result"]
        risk_output = state["financial_risk_result"]
        result = run_loan_decision_agent(application, profile_output, risk_output)
        return {**state, "loan_decision_result": result, "final_decision": result.classification}
    except Exception as exc:
        logger.error("Loan Decision Agent failed: %s", exc)
        return {**state, "error": f"Loan Decision Agent error: {exc}", "status": "error"}


def node_compliance_action(state: WorkflowState) -> WorkflowState:
    logger.info("Invoking Compliance and Action Orchestrator Agent")
    try:
        application: LoanApplication = state["loan_application"]
        decision_output = state["loan_decision_result"]
        result = run_compliance_action_orchestrator_agent(decision_output, application.applicant_id)
        return {**state, "compliance_action_result": result, "status": "completed"}
    except Exception as exc:
        logger.error("Compliance and Action Orchestrator Agent failed: %s", exc)
        return {**state, "error": f"Compliance Agent error: {exc}", "status": "error"}


def node_error_handler(state: WorkflowState) -> WorkflowState:
    logger.error("Workflow reached error state: %s", state.get("error"))
    return {**state, "status": "error"}


# ---- Graph construction ----

def build_loan_workflow() -> StateGraph:
    workflow = StateGraph(WorkflowState)

    workflow.add_node("applicant_profile", node_applicant_profile)
    workflow.add_node("financial_risk_analysis", node_financial_risk)
    workflow.add_node("loan_decision", node_loan_decision)
    workflow.add_node("compliance_action", node_compliance_action)
    workflow.add_node("error_handler", node_error_handler)

    workflow.set_entry_point("applicant_profile")

    workflow.add_conditional_edges(
        "applicant_profile",
        route_after_profile,
        {"financial_risk_analysis": "financial_risk_analysis", "error_handler": "error_handler"},
    )
    workflow.add_conditional_edges(
        "financial_risk_analysis",
        route_after_risk,
        {"loan_decision": "loan_decision", "error_handler": "error_handler"},
    )
    workflow.add_conditional_edges(
        "loan_decision",
        route_after_decision,
        {"compliance_action": "compliance_action", "error_handler": "error_handler"},
    )
    workflow.add_conditional_edges(
        "compliance_action",
        route_after_compliance,
        {"end": END, "error_handler": "error_handler"},
    )
    workflow.add_edge("error_handler", END)

    return workflow.compile()


def run_loan_workflow(application: LoanApplication) -> WorkflowState:
    """Entry point: run the full loan decisioning workflow."""
    graph = build_loan_workflow()
    initial_state: WorkflowState = {
        "loan_application": application,
        "applicant_profile_result": None,
        "financial_risk_result": None,
        "loan_decision_result": None,
        "compliance_action_result": None,
        "final_decision": None,
        "status": "pending",
        "error": None,
    }
    final_state = graph.invoke(initial_state)
    return final_state
