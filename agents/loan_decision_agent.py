"""
Loan Decision Agent
MCP Server: DecisionSynthesis
Invokes DecisionSynthesis and Anthropic Claude Sonnet 4.6 to produce the final decision.
"""
import os
import json
import logging
from pathlib import Path

from models.loan_application import LoanApplication
from models.agent_outputs import ApplicantProfileOutput, FinancialRiskOutput, LoanDecisionOutput
from mcp_client import call_mcp_tool_sync

logger = logging.getLogger(__name__)

MCP_DECISION_SYNTHESIS_URL = os.getenv("MCP_DECISION_SYNTHESIS_URL", "http://localhost:8003")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL_NAME = os.getenv("ANTHROPIC_MODEL_NAME", "global.anthropic.claude-sonnet-4-6")
ANTHROPIC_BASE_URL = os.getenv("ANTHROPIC_BASE_URL", None)
MOCK_LLM_MODE = os.getenv("MOCK_LLM_MODE", "false").lower() == "true"

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "loan_decision_prompt.txt"

_VALID_CLASSIFICATIONS = {"Approved", "Rejected", "Requires Manual Review"}
_NORMALIZE_MAP = {
    "approve": "Approved",
    "approved": "Approved",
    "reject": "Rejected",
    "rejected": "Rejected",
    "review": "Requires Manual Review",
    "requires manual review": "Requires Manual Review",
    "requires review": "Requires Manual Review",
    "manual review": "Requires Manual Review",
    "pending": "Requires Manual Review",
    "escalated": "Requires Manual Review",
    "conditional approval": "Requires Manual Review",
}


def _normalize_classification(raw: str) -> str:
    if raw in _VALID_CLASSIFICATIONS:
        return raw
    normalized = _NORMALIZE_MAP.get(raw.lower().strip())
    if normalized:
        return normalized
    # Default to manual review for ambiguous values
    return "Requires Manual Review"


def run_loan_decision_agent(
    application: LoanApplication,
    profile_output: ApplicantProfileOutput,
    risk_output: FinancialRiskOutput,
) -> LoanDecisionOutput:
    """
    1. Calls DecisionSynthesis MCP to compute preliminary synthesis.
    2. Invokes Claude Sonnet 4.6 (or mock) for final structured decision.
    """
    # Step 1: Call DecisionSynthesis MCP via proper FastMCP Client
    synthesis = call_mcp_tool_sync(
        MCP_DECISION_SYNTHESIS_URL,
        "synthesize_decision",
        applicant_id=application.applicant_id,
        credit_score=application.credit_score,
        income=application.applicant_profile.income,
        loan_amount=application.loan_amount,
        tenure=application.tenure,
        existing_liabilities=application.existing_liabilities,
        employment_type=application.applicant_profile.employment_type,
        income_stability_score=profile_output.income_stability_score,
        employment_risk=profile_output.employment_risk,
        debt_to_income_ratio=risk_output.debt_to_income_ratio,
        credit_score_risk_level=risk_output.credit_score_risk_level,
        loan_amount_risk=risk_output.loan_amount_risk,
        anomaly_detection=risk_output.anomaly_detection,
    )

    # Step 2: Invoke LLM
    loan_data_str = json.dumps({
        "applicant_id": application.applicant_id,
        "age": application.applicant_profile.age,
        "income": application.applicant_profile.income,
        "employment_type": application.applicant_profile.employment_type,
        "credit_score": application.credit_score,
        "loan_amount": application.loan_amount,
        "tenure": application.tenure,
        "existing_liabilities": application.existing_liabilities,
        "location": application.location,
    }, indent=2)

    profile_str = json.dumps({
        "income_stability_score": profile_output.income_stability_score,
        "employment_risk": profile_output.employment_risk,
        "credit_history_summary": profile_output.credit_history_summary,
        "application_completeness_flags": profile_output.application_completeness_flags,
    }, indent=2)

    risk_str = json.dumps({
        "debt_to_income_ratio": risk_output.debt_to_income_ratio,
        "credit_score_risk_level": risk_output.credit_score_risk_level,
        "loan_amount_risk": risk_output.loan_amount_risk,
        "anomaly_detection": risk_output.anomaly_detection,
        "reasoning": risk_output.reasoning,
    }, indent=2)

    if MOCK_LLM_MODE:
        logger.warning("[MOCK LLM MODE] Returning mock loan decision. Not a real AI response.")
        llm_result = _mock_decision(synthesis)
    else:
        llm_result = _call_claude(
            loan_data_str=loan_data_str,
            profile_str=profile_str,
            risk_str=risk_str,
            synthesis_context=synthesis.get("synthesis_context", ""),
        )

    # Normalize classification to exact business values
    llm_result["classification"] = _normalize_classification(llm_result.get("classification", ""))

    return LoanDecisionOutput(
        classification=llm_result["classification"],
        risk_score=float(llm_result.get("risk_score", synthesis.get("risk_score", 50.0))),
        confidence_level=float(llm_result.get("confidence_level", synthesis.get("confidence_level", 0.5))),
        key_decision_factors=llm_result.get(
            "key_decision_factors", synthesis.get("key_decision_factors", [])
        ),
        explanation=llm_result.get("explanation", "Decision based on supplied application data."),
    )


def _call_claude(
    loan_data_str: str,
    profile_str: str,
    risk_str: str,
    synthesis_context: str,
) -> dict:
    from anthropic import Anthropic

    prompt_template = PROMPT_PATH.read_text()
    prompt = prompt_template.format(
        loan_application_data=loan_data_str,
        applicant_profile_output=profile_str,
        financial_risk_output=risk_str,
        synthesis_context=synthesis_context,
    )

    client_kwargs = {"api_key": ANTHROPIC_API_KEY}
    if ANTHROPIC_BASE_URL:
        client_kwargs["base_url"] = ANTHROPIC_BASE_URL

    client = Anthropic(**client_kwargs)
    message = client.messages.create(
        model=ANTHROPIC_MODEL_NAME,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = message.content[0].text.strip()
    # Strip markdown code fences if present
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
    return json.loads(raw_text)


def _mock_decision(synthesis: dict) -> dict:
    """
    MOCK LLM MODE — returns deterministic structured output.
    Identified as mock in the explanation field.
    """
    return {
        "classification": synthesis.get("preliminary_classification", "Requires Manual Review"),
        "risk_score": synthesis.get("risk_score", 50.0),
        "confidence_level": synthesis.get("confidence_level", 0.65),
        "key_decision_factors": synthesis.get("key_decision_factors", ["Automated mock assessment"]),
        "explanation": (
            "[MOCK LLM MODE — no real AI inference performed] "
            "Decision derived from DecisionSynthesis rule engine. "
            f"Preliminary classification: {synthesis.get('preliminary_classification')}. "
            f"Risk score: {synthesis.get('risk_score', 50.0):.1f}/100."
        ),
    }
