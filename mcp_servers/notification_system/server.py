"""
NotificationSystem MCP Server
Simulates notifications, generates case IDs, records actions, and produces summaries.
No real notification service is connected.
"""
import os
import uuid
from datetime import datetime, timezone
from fastmcp import FastMCP
from pydantic import BaseModel
from typing import Literal

mcp = FastMCP("NotificationSystem MCP Server")

# In-memory action log for the proof of concept
ACTION_LOG = []


class NotificationRequest(BaseModel):
    applicant_id: str
    classification: Literal["Approved", "Rejected", "Requires Manual Review"]
    risk_score: float
    explanation: str


class NotificationResponse(BaseModel):
    action_taken: str
    notification_sent: bool
    case_id: str
    timestamp: datetime
    summary: str


@mcp.tool()
def send_notification(
    applicant_id: str,
    classification: str,
    risk_score: float,
    explanation: str,
) -> dict:
    case_id = f"CASE-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.now(timezone.utc)

    action_map = {
        "Approved": "Loan approval letter prepared. File forwarded to disbursement queue.",
        "Rejected": "Rejection notice prepared. File archived.",
        "Requires Manual Review": "Case escalated to human underwriter queue for manual review.",
    }

    summary_map = {
        "Approved": (
            f"Application {applicant_id} APPROVED. "
            f"Risk score: {risk_score:.1f}. {explanation}"
        ),
        "Rejected": (
            f"Application {applicant_id} REJECTED. "
            f"Risk score: {risk_score:.1f}. {explanation}"
        ),
        "Requires Manual Review": (
            f"Application {applicant_id} requires MANUAL REVIEW. "
            f"Risk score: {risk_score:.1f}. {explanation}"
        ),
    }

    action_taken = action_map[classification]
    summary = summary_map[classification]

    # Record action (proof-of-concept simulation)
    ACTION_LOG.append({
        "case_id": case_id,
        "applicant_id": applicant_id,
        "classification": classification,
        "action_taken": action_taken,
        "timestamp": now.isoformat(),
    })

    return {
        "action_taken": action_taken,
        "notification_sent": True,
        "case_id": case_id,
        "timestamp": now.isoformat(),
        "summary": summary,
    }


@mcp.tool()
def get_action_log() -> dict:
    return {"actions": ACTION_LOG}


app = mcp.http_app()


if __name__ == "__main__":
    port = int(os.getenv("MCP_NOTIFICATION_SYSTEM_PORT", "8004"))
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=port,
    )
