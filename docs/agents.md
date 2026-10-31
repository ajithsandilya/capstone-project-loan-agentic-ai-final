# Agent-to-MCP-Server Communication

## Agent Communication Map

```mermaid
graph LR
    A1[Applicant Profile Agent] -->|POST /tools/get_applicant_context| MCP1[(ApplicantDB\n:8001)]
    A2[Financial Risk Analysis Agent] -->|POST /tools/get_risk_rules| MCP2[(RiskRulesDB\n:8002)]
    A3[Loan Decision Agent] -->|POST /tools/synthesize_decision| MCP3[(DecisionSynthesis\n:8003)]
    A3 -->|messages.create| LLM[Claude Sonnet 4.6]
    A4[Compliance and Action\nOrchestrator Agent] -->|POST /tools/send_notification| MCP4[(NotificationSystem\n:8004)]
```

## Agent Responsibilities

### Applicant Profile Agent
- **MCP Server:** ApplicantDB
- Fetches contextual applicant information from ApplicantDB
- Analyses the applicant profile
- **Output:** Income Stability Score, Employment Risk, Credit History Summary, Application Completeness Flags

### Financial Risk Analysis Agent
- **MCP Server:** RiskRulesDB
- Fetches configurable proof-of-concept risk rules from RiskRulesDB
- Analyses financial risk for the application
- **Output:** Debt-to-Income Ratio, Credit Score Risk Level, Loan Amount Risk, Anomaly Detection, Reasoning

### Loan Decision Agent
- **MCP Server:** DecisionSynthesis
- **LLM:** Anthropic Claude Sonnet 4.6
- Receives profile and risk outputs
- Calls DecisionSynthesis MCP for preliminary synthesis
- Invokes Claude for final structured decision
- **Output:** Classification, Risk Score, Confidence Level, Key Decision Factors, Explanation

### Compliance and Action Orchestrator Agent
- **MCP Server:** NotificationSystem
- Receives the loan decision
- Calls NotificationSystem MCP to simulate notifications and record actions
- **Output:** Action Taken, Notification Sent, Case ID, Timestamp, Summary
