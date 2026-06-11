"""
agent/nodes/analyze_amount.py
==============================
NODE 2 — analyze_amount

Reads:   state["transaction"]["amount"], state["avg_spend"]
Writes:  state["amount_score"]

Scoring table:
  spend_ratio = amount / avg_spend
  < 2x   →  0   (normal)
  2–5x   → 15   (elevated)
  5–10x  → 25   (high)
  > 10x  → 40   (critical)

Pure Python — no DB, no LLM, no external calls.
"""

from agent.state import AgentState
import logging 
logger = logging.getLogger(__name__) 


def analyze_amount(state: AgentState) -> AgentState:
    amount    = state["transaction"]["amount"]
    avg_spend = state["avg_spend"]

    # Guard against zero avg (brand-new customer with no history)
    if avg_spend == 0:
        ratio = 99.0
    else:
        ratio = amount / avg_spend

    if ratio < 2:
        score = 0
    elif ratio < 5:
        score = 15
    elif ratio < 10:
        score = 25
    else:
        score = 40
    logger.info(f"amount_score={score}, ratio={ratio:.2f}x") 
    return {**state, "amount_score": score}