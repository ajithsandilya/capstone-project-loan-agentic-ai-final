"""
NotificationSystem MCP Server
Simulates notifications, generates case IDs, records actions, and produces summaries.
No real notification service is connected.
"""
import os
import uuid
from datetime import datetime, timezone
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Literal

app = FastAPI(title="NotificationSystem MCP Server")

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


@app.get("/health")
def health():
    return {"status": "ok", "server": "NotificationSystem"}


@app.post("/tools/send_notification", response_model=NotificationResponse)
def send_notification(req: NotificationRequest) -> NotificationResponse:
    case_id = f"CASE-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.now(timezone.utc)

    action_map = {
        "Approved": "Loan approval letter prepared. File forwarded to disbursement queue.",
        "Rejected": "Rejection notice prepared. File archived.",
        "Requires Manual Review": "Case escalated to human underwriter queue for manual review.",
    }

    summary_map = {
        "Approved": (
            f"Application {req.applicant_id} APPROVED. "
            f"Risk score: {req.risk_score:.1f}. {req.explanation}"
        ),
        "Rejected": (
            f"Application {req.applicant_id} REJECTED. "
            f"Risk score: {req.risk_score:.1f}. {req.explanation}"
        ),
        "Requires Manual Review": (
            f"Application {req.applicant_id} requires MANUAL REVIEW. "
            f"Risk score: {req.risk_score:.1f}. {req.explanation}"
        ),
    }

    action_taken = action_map[req.classification]
    summary = summary_map[req.classification]

    # Record action (proof-of-concept simulation)
    ACTION_LOG.append({
        "case_id": case_id,
        "applicant_id": req.applicant_id,
        "classification": req.classification,
        "action_taken": action_taken,
        "timestamp": now.isoformat(),
    })

    return NotificationResponse(
        action_taken=action_taken,
        notification_sent=True,  # Simulated
        case_id=case_id,
        timestamp=now,
        summary=summary,
    )


@app.get("/tools/get_action_log")
def get_action_log():
    return {"actions": ACTION_LOG}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("MCP_NOTIFICATION_SYSTEM_PORT", "8004"))
    uvicorn.run(app, host="0.0.0.0", port=port)
