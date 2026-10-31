"""
Compliance and Action Orchestrator Agent
MCP Server: NotificationSystem
Performs final action orchestration after the loan decision is made.
"""
import os
import httpx
from models.agent_outputs import LoanDecisionOutput, ComplianceActionOutput

MCP_NOTIFICATION_SYSTEM_URL = os.getenv("MCP_NOTIFICATION_SYSTEM_URL", "http://localhost:8004")


def run_compliance_action_orchestrator_agent(
    decision_output: LoanDecisionOutput,
    applicant_id: str,
) -> ComplianceActionOutput:
    """
    Receives the Loan Decision Agent result, calls NotificationSystem MCP,
    and produces the final structured compliance and action output.
    """
    response = httpx.post(
        f"{MCP_NOTIFICATION_SYSTEM_URL}/tools/send_notification",
        json={
            "applicant_id": applicant_id,
            "classification": decision_output.classification,
            "risk_score": decision_output.risk_score,
            "explanation": decision_output.explanation,
        },
        timeout=10.0,
    )
    response.raise_for_status()
    result = response.json()

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
