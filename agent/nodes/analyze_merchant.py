"""
agent/nodes/analyze_merchant.py
================================
NODE 4 — analyze_merchant

Reads:   merchant_category, common_categories
Writes:  merchant_score  (max 15)

Scoring rules:
  +10  if category is in the HIGH_RISK set
  +5   if category is NOT in customer's common_categories
  Max score capped at 15.

Pure Python — no DB, no LLM, no external calls.
"""

from agent.state import AgentState

HIGH_RISK_CATEGORIES = {
    "JEWELRY",
    "ELECTRONICS",
    "GIFT_CARDS",
    "CRYPTO",
    "WIRE_TRANSFER",
    "FOREX",
}


def analyze_merchant(state: AgentState) -> AgentState:
    category          = state["transaction"]["merchant_category"]
    common_categories = state["common_categories"]

    score = 0

    if category in HIGH_RISK_CATEGORIES:
        score += 10

    if category not in common_categories:
        score += 5

    return {**state, "merchant_score": min(score, 15)}