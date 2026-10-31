# Proof-of-Concept Assumptions

## Overview

This document records every assumption made to produce a runnable proof of concept.
None of these assumptions represent real banking policy, legal requirements, or regulatory guidance.

---

## 1. Numeric Risk Thresholds

All numeric thresholds are stored in `config/poc_rules.yaml` and are clearly labelled as configurable proof-of-concept rules.

| Parameter | Assumption | File |
|---|---|---|
| Income stability bands | High ≥ 80 000, Medium ≥ 40 000, Low < 40 000 | poc_rules.yaml |
| Credit score bands | Excellent ≥ 750, Good ≥ 650, Fair ≥ 550, Poor < 550 | poc_rules.yaml |
| Debt-to-Income thresholds | Low ≤ 30%, Medium ≤ 50%, High > 50% | poc_rules.yaml |
| Loan amount bands | Low ≤ 100 000, Medium ≤ 500 000, High > 500 000 | poc_rules.yaml |
| Loan-to-income anomaly | Ratio > 10× flags anomaly | poc_rules.yaml |
| Age validity | 18–75 years | poc_rules.yaml |
| Tenure minimum | ≥ 6 months | poc_rules.yaml |
| Risk score approval | Score ≤ 35 → Approved | poc_rules.yaml |
| Risk score manual review | Score ≤ 65 → Requires Manual Review | poc_rules.yaml |
| Risk score rejection | Score > 65 → Rejected | poc_rules.yaml |

---

## 2. Applicant Data

ApplicantDB uses local in-memory mock data.
No real applicant database exists.
Mock data is sufficient to evaluate income stability, employment risk, credit history, and application completeness for the proof of concept.

---

## 3. Notification System

NotificationSystem simulates notifications only.
No real email, SMS, Teams, or push notification service is connected.
Case IDs are UUID-based sequential identifiers generated at runtime.

---

## 4. Zero-Income Handling

If an applicant reports zero income, Debt-to-Income Ratio calculation is skipped.
The agent returns a "High Risk" assessment with reasoning that zero income prevents ratio calculation.

---

## 5. LLM Integration

The Loan Decision Agent calls Anthropic Claude Sonnet 4.6 to produce the final structured classification.
A mock LLM mode is available (`MOCK_LLM_MODE=true`) that returns deterministic structured output without an API key.
Mock mode is clearly identified in all responses and logs.

---

## 6. MCP Communication

MCP servers run as separate FastAPI-based HTTP services on configurable ports.
In production, MCP servers would connect to real data sources.
All MCP tools return mock or computed data for this proof of concept.

---

## 7. Agent Execution Model

Agents are Python functions invoked synchronously by the LangGraph orchestrator.
Each agent calls its corresponding MCP server via HTTP.
Error handling is included; agent failures propagate error state through the workflow.

---

## 8. Risk Score Calculation

Risk Score is a weighted composite (0–100 scale) using:
- Credit Score Weight: 35%
- Debt-to-Income Ratio Weight: 30%
- Loan Amount Risk Weight: 20%
- Employment Risk Weight: 15%

This formula is a proof-of-concept assumption, not a validated actuarial model.

---

## 9. Confidence Level

Confidence Level is derived from the spread of individual risk indicators.
Higher agreement across indicators produces higher confidence.
This is a heuristic assumption for the proof of concept.

---

## 10. Timestamps

All timestamps are UTC ISO-8601 strings generated at runtime.
