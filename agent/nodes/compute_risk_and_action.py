"""
agent/nodes/compute_risk_and_action.py
=======================================
NODE 6 — compute_risk_and_action

Reads:   amount_score, location_score, merchant_score, pattern_score
Writes:  risk_score, risk_level, recommendation

Thresholds:
  0  – 30  → LOW      / ALLOW
  31 – 55  → MEDIUM   / SEND_OTP
  56 – 75  → HIGH     / ESCALATE
  76 – 100 → CRITICAL / BLOCK_CARD

CRITICAL DESIGN RULE:
  This is 100% pure Python.
  The LLM CANNOT touch risk_score or recommendation.
  They are injected into generate_report as fixed values.
"""

from agent.state import AgentState


def compute_risk_and_action(state: AgentState) -> AgentState:
    risk_score = (
        state["amount_score"]   +
        state["location_score"] +
        state["merchant_score"] +
        state["pattern_score"]
    )

    if risk_score <= 30:
        risk_level     = "LOW"
        recommendation = "ALLOW"
    elif risk_score <= 55:
        risk_level     = "MEDIUM"
        recommendation = "SEND_OTP"
    elif risk_score <= 75:
        risk_level     = "HIGH"
        recommendation = "ESCALATE"
    else:
        risk_level     = "CRITICAL"
        recommendation = "BLOCK_CARD"

    return {
        **state,
        "risk_score":     risk_score,
        "risk_level":     risk_level,
        "recommendation": recommendation,
    }