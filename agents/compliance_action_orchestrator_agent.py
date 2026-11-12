"""
Compliance and Action Orchestrator Agent
MCP Server: NotificationSystem
Performs final action orchestration after the loan decision is made.
"""
import os
import logging
from models.agent_outputs import LoanDecisionOutput, ComplianceActionOutput
from mcp_client import call_mcp_tool_sync

logger = logging.getLogger(__name__)

MCP_NOTIFICATION_SYSTEM_URL = os.getenv("MCP_NOTIFICATION_SYSTEM_URL", "http://localhost:8004")


def run_compliance_action_orchestrator_agent(
    decision_output: LoanDecisionOutput,
    applicant_id: str,
) -> ComplianceActionOutput:
    """
    Receives the Loan Decision Agent result, calls NotificationSystem MCP,
    and produces the final structured compliance and action output.
    """
    result = call_mcp_tool_sync(
        MCP_NOTIFICATION_SYSTEM_URL,
        "send_notification",
        applicant_id=applicant_id,
        classification=decision_output.classification,
        risk_score=decision_output.risk_score,
        explanation=decision_output.explanation,
    )

    from datetime import datetime
    ts = result.get("timestamp")
    if isinstance(ts, str):
        timestamp = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    else:
        from datetime import timezone
        timestamp = datetime.now(timezone.utc)

    return ComplianceActionOutput(
        action_taken=result["action_taken"],
        notification_sent=result["notification_sent"],
        case_id=result["case_id"],
        timestamp=timestamp,
        summary=result["summary"],
    )
