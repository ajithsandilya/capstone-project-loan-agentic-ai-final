# Multi-Agent Agentic AI Loan Decisioning System

> **Proof of concept.** Not production-ready. Not legally or regulatorily compliant.

---

## Problem Statement

Manual or rule-heavy loan approval processes are slow, inconsistent, and difficult to scale. This system uses a Multi-Agent Agentic AI approach to analyse loan applications and classify them as **Approved**, **Rejected**, or **Requires Manual Review**.

---

## Business Objectives

- Automate loan application analysis using Agentic AI
- Improve decision speed and consistency
- Provide explainable and auditable decisions
- Adopt a scalable, loosely coupled microservices architecture

---

## Input Parameters

| Field | Type | Description |
|---|---|---|
| `applicant_id` | string | Unique applicant identifier |
| `applicant_profile.age` | integer | Applicant age in years |
| `applicant_profile.income` | float | Annual income |
| `applicant_profile.employment_type` | string | Employment type |
| `credit_score` | integer | Credit score (300–850) |
| `loan_amount` | float | Requested loan amount |
| `tenure` | integer | Loan tenure in months |
| `existing_liabilities` | float | Total existing liabilities |
| `location` | string | Applicant location |
| `application_timestamp` | datetime | Application timestamp (auto-generated if omitted) |

---

## Architecture Overview

Five layers:

1. **Presentation Layer** — Streamlit chatbot UI
2. **Microservice Layer** — FastAPI REST API
3. **Orchestration Layer** — LangGraph workflow engine
4. **Agent Layer** — Four specialised Python agents
5. **Communication Layer** — Four MCP servers

See [docs/architecture.md](docs/architecture.md) for the Mermaid diagram.

---

## Four Agents

| Agent | MCP Server | Outputs |
|---|---|---|
| Applicant Profile Agent | ApplicantDB | Income Stability Score, Employment Risk, Credit History Summary, Completeness Flags |
| Financial Risk Analysis Agent | RiskRulesDB | DTI Ratio, Credit Score Risk Level, Loan Amount Risk, Anomaly Detection, Reasoning |
| Loan Decision Agent | DecisionSynthesis + Claude | Classification, Risk Score, Confidence Level, Key Decision Factors, Explanation |
| Compliance and Action Orchestrator Agent | NotificationSystem | Action Taken, Notification Sent, Case ID, Timestamp, Summary |

---

## Four MCP Servers

| Server | Port | Purpose |
|---|---|---|
| ApplicantDB | 8001 | In-memory mock applicant contextual data |
| RiskRulesDB | 8002 | Configurable proof-of-concept risk rules from `config/poc_rules.yaml` |
| DecisionSynthesis | 8003 | Weighted risk score and preliminary classification |
| NotificationSystem | 8004 | Simulated notifications, case ID generation, action recording |

---

## Required Workflow

1. User submits loan application through Streamlit chatbot UI
2. UI forwards data to FastAPI microservice
3. Microservice passes validated request to LangGraph orchestrator
4. Orchestrator invokes agents through MCP servers
5. Agents fetch contextual data, perform analysis, return results
6. Orchestrator synthesises outcomes and invokes Claude Sonnet 4.6
7. Final decision propagated back to Streamlit chatbot UI

---

## Technology Stack

| Technology | Role |
|---|---|
| Streamlit + Python | Chatbot UI |
| FastAPI + Python | Microservice |
| LangGraph + LangChain | Orchestration |
| FastMCP | MCP framework |
| FastAPI-based agents | Agent implementation |
| Anthropic Claude Sonnet 4.6 | LLM |
| Anthropic SDK | Agent SDK |
| Python 3.12 | Runtime |

---

## Installation

```bash
# Clone or extract the project
cd loan-agentic-ai

# Install dependencies
pip install --break-system-packages -r requirements.txt
# Or inside a virtual environment:
# python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
```

---

## Environment Variable Setup

```bash
cp .env.example .env
# Edit .env:
# ANTHROPIC_API_KEY=sk-ant-...   (required for real mode)
# ANTHROPIC_MODEL_NAME=claude-sonnet-4-6
# MOCK_LLM_MODE=false            (set to true to skip the API key)
# FASTAPI_URL=http://localhost:8000
```

---

## How to Start the MCP Servers

Open four terminals (or run each in the background):

```bash
# Terminal 1 — ApplicantDB
python3 -m uvicorn mcp_servers.applicant_db.server:app --port 8001

# Terminal 2 — RiskRulesDB
python3 -m uvicorn mcp_servers.risk_rules_db.server:app --port 8002

# Terminal 3 — DecisionSynthesis
python3 -m uvicorn mcp_servers.decision_synthesis.server:app --port 8003

# Terminal 4 — NotificationSystem
python3 -m uvicorn mcp_servers.notification_system.server:app --port 8004
```

---

## How to Start FastAPI

```bash
# Terminal 5
python3 -m uvicorn microservice.main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

---

## How to Start Streamlit

```bash
# Terminal 6
python3 -m streamlit run app/streamlit_app.py
```

Opens at: http://localhost:8501

---

## How to Use Mock LLM Mode

Set `MOCK_LLM_MODE=true` in your `.env` file (or export it) before starting FastAPI.

```bash
MOCK_LLM_MODE=true python3 -m uvicorn microservice.main:app --reload --port 8000
```

Mock mode:
- Does not require an `ANTHROPIC_API_KEY`
- Uses the DecisionSynthesis rule engine for the decision
- Clearly marks responses with `[MOCK LLM MODE]` in the explanation field
- Preserves the same request and response schemas as real mode

---

## How to Run Tests

```bash
python3 -m pytest tests/ -v
```

All 31 tests cover the 21 required test cases listed in the specification.

---

## Example Loan Application

```json
{
  "applicant_id": "APP001",
  "applicant_profile": {
    "age": 35,
    "income": 75000,
    "employment_type": "SALARIED"
  },
  "credit_score": 720,
  "loan_amount": 150000,
  "tenure": 36,
  "existing_liabilities": 15000,
  "location": "New York"
}
```

---

## Example Output — Approved

```json
{
  "applicant_id": "APP001",
  "classification": "Approved",
  "risk_score": 24.5,
  "confidence_level": 0.90,
  "key_decision_factors": [
    "Credit score 720 is within acceptable range",
    "Debt-to-income ratio 0.20 is acceptable",
    "Stable employment type"
  ],
  "explanation": "The applicant presents a strong credit profile with a manageable debt load and stable employment. The requested loan amount is within acceptable risk parameters.",
  "action_taken": "Loan approval letter prepared. File forwarded to disbursement queue.",
  "notification_sent": true,
  "case_id": "CASE-A1B2C3D4",
  "timestamp": "2024-01-15T10:30:00Z",
  "summary": "Application APP001 APPROVED. Risk score: 24.5.",
  "status": "completed",
  "mock_mode": false
}
```

## Example Output — Rejected

```json
{
  "classification": "Rejected",
  "risk_score": 83.0,
  "confidence_level": 0.92,
  "key_decision_factors": [
    "Credit score 380 indicates elevated risk",
    "Debt-to-income ratio 0.90 is elevated",
    "High loan amount risk"
  ],
  "explanation": "The applicant has a very low credit score and an extremely high debt-to-income ratio. The requested loan amount exceeds acceptable thresholds for this risk profile.",
  "action_taken": "Rejection notice prepared. File archived."
}
```

## Example Output — Requires Manual Review

```json
{
  "classification": "Requires Manual Review",
  "risk_score": 51.0,
  "confidence_level": 0.62,
  "key_decision_factors": [
    "Borderline credit score 610",
    "Debt-to-income ratio 0.36 is in the medium range"
  ],
  "explanation": "The application presents a mixed risk profile. While income and employment are acceptable, the credit score and loan amount require a human underwriter to make a final determination.",
  "action_taken": "Case escalated to human underwriter queue for manual review."
}
```

---

## Proof-of-Concept Limitations

1. **No real database.** ApplicantDB uses in-memory mock data.
2. **Simulated notifications only.** No email, SMS, or push notification service is connected.
3. **Configurable thresholds are illustrative.** Risk rules in `config/poc_rules.yaml` are not validated banking policy.
4. **No authentication or authorisation.** Any caller can submit applications.
5. **In-memory state.** Application status is lost when FastAPI restarts.
6. **Sequential agent execution.** Agents run in order; no parallel execution in this proof of concept.
7. **Single-process deployment.** All services must be started manually as separate processes.
8. **Not production-ready.** No TLS, rate limiting, secrets management, or persistent storage.
9. **Not legally compliant.** No regulatory review has been performed.
