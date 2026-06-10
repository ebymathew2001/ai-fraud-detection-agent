"""
agent/nodes/generate_report.py
================================
NODE 7 — generate_report

Reads:   all state (transaction, customer, all scores, fraud_patterns)
Writes:  state["report"]  (full structured dict)

This is the ONLY node that calls the Groq LLM.

CRITICAL RULE:
  risk_score, risk_level, and recommendation are INJECTED into the
  system prompt as fixed, pre-computed values.
  The LLM writes ONLY the "reasons" list — it cannot override the score
  or change the recommendation under any circumstance.
"""

import os
import json
import uuid
from datetime import datetime, timezone

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

from agent.state import AgentState

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


def generate_report(state: AgentState) -> AgentState:
    txn            = state["transaction"]
    customer       = state["customer"]
    risk_score     = state["risk_score"]
    risk_level     = state["risk_level"]
    recommendation = state["recommendation"]
    avg_spend      = state["avg_spend"]
    patterns       = state["fraud_patterns"]

    # ── System prompt — LLM is told the score is fixed ────────────
    system_prompt = f"""You are a banking fraud analyst AI assistant.

A deterministic scoring engine has already computed the fraud risk for a transaction.
Your ONLY job is to write 3 to 5 clear, specific reasons that explain WHY this
transaction received the given score. Base your reasons on the transaction data provided.

FIXED VALUES — you MUST NOT change these:
  risk_score:     {risk_score}
  risk_level:     {risk_level}
  recommendation: {recommendation}

Return ONLY a valid JSON object in exactly this format.
No markdown, no code fences, no extra text — just the JSON:
{{
  "reasons": [
    "First reason here.",
    "Second reason here.",
    "Third reason here."
  ]
}}
"""

    # ── Human prompt — full transaction context ────────────────────
    human_prompt = f"""Transaction to explain:

  TXN ID:   {txn['txn_id']}
  Customer: {customer['name']} (home city: {customer['home_city']})
  Amount:   Rs.{txn['amount']:.0f}   (20-transaction average: Rs.{avg_spend:.0f})
  Merchant: {txn['merchant_name']} ({txn['merchant_category']})
  Location: {txn['transaction_location']}   (last known location: {state['last_known_location']})

Score breakdown:
  Amount score:    {state['amount_score']}  / 40
  Location score:  {state['location_score']} / 30
  Merchant score:  {state['merchant_score']} / 15
  Pattern score:   {state['pattern_score']}  / 15
  ─────────────────────────
  Total:           {risk_score} / 100  →  {risk_level}  →  {recommendation}

Matched fraud patterns from the knowledge base:
{chr(10).join(f"  • {p}" for p in patterns)}

Write the reasons list explaining this specific assessment."""

    # ── Call Groq LLM ──────────────────────────────────────────────
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=GROQ_API_KEY,
        temperature=0.3,
        max_tokens=800,
    )

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt),
    ])

    # ── Parse the JSON response ────────────────────────────────────
    raw = response.content.strip()

    # Strip accidental markdown code fences if model adds them
    if raw.startswith("```"):
        parts = raw.split("```")
        raw   = parts[1] if len(parts) > 1 else raw
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        llm_output = json.loads(raw)
        reasons    = llm_output.get("reasons", [])
        if not reasons:
            raise ValueError("Empty reasons list")
    except (json.JSONDecodeError, ValueError):
        # Fallback — deterministic reasons if LLM output is unparseable
        reasons = [
            f"Amount Rs.{txn['amount']:.0f} is {txn['amount']/avg_spend:.1f}x the customer's 20-transaction average of Rs.{avg_spend:.0f}.",
            f"Transaction location '{txn['transaction_location']}' classified as '{state['location_matched']}' relative to known customer locations.",
            f"Merchant category '{txn['merchant_category']}' scored {state['merchant_score']}/15 on the merchant risk scale.",
        ]

    # ── Build the full report dict ─────────────────────────────────
    investigation_id = f"inv_{uuid.uuid4().hex[:8]}"
    created_at       = datetime.now(timezone.utc).isoformat()

    report = {
        "investigation_id": investigation_id,
        "txn_id":           txn["txn_id"],
        "customer_name":    customer["name"],
        "risk_score":       risk_score,       # from compute_risk_and_action — NOT from LLM
        "risk_level":       risk_level,       # from compute_risk_and_action — NOT from LLM
        "recommendation":   recommendation,   # from compute_risk_and_action — NOT from LLM
        "reasons":          reasons,          # ← the only thing the LLM wrote
        "amount":           txn["amount"],
        "merchant":         txn["merchant_name"],
        "category":         txn["merchant_category"],
        "location":         txn["transaction_location"],
        "last_known_location": state["last_known_location"],
        "avg_spend":        avg_spend,
        "sub_scores": {
            "amount_score":   state["amount_score"],
            "location_score": state["location_score"],
            "merchant_score": state["merchant_score"],
            "pattern_score":  state["pattern_score"],
        },
        "matched_patterns": patterns,
        "created_at":       created_at,
    }

    return {**state, "report": report}