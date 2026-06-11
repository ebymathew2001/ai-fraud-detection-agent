"""
agent/nodes/analyze_location.py
================================
NODE 3 — analyze_location

Reads:   transaction_location, last_known_location,
         common_locations, customer["home_city"]
Writes:  location_score, location_matched

Scoring table:
  == last_known_location  →  0, "last_known"
  in common_locations     → 10, "common"
  same broad region       → 20, "region"   (both Indian cities)
  completely novel        → 30, "novel"

Pure Python — no DB, no LLM, no external calls.
"""

from agent.state import AgentState
import logging 
logger = logging.getLogger(__name__) 

# All Indian cities present in our seed data.
# Extend this set if you add more cities to transactions.
INDIA_CITIES = {
    "Mumbai", "Delhi", "Chennai", "Bangalore", "Hyderabad",
    "Kolkata", "Pune", "Ahmedabad", "Jaipur", "Noida",
    "Surat", "Lucknow", "Kanpur", "Nagpur", "Indore",
}


def _is_india(city: str) -> bool:
    return city in INDIA_CITIES


def analyze_location(state: AgentState) -> AgentState:
    txn_location     = state["transaction"]["transaction_location"]
    last_known       = state["last_known_location"]
    common_locations = state["common_locations"]
    home_city        = state["customer"]["home_city"]

    if txn_location == last_known:
        score   = 0
        matched = "last_known"

    elif txn_location in common_locations:
        score   = 10
        matched = "common"

    elif _is_india(txn_location) and _is_india(home_city):
        # Both cities are in India → same broad region
        score   = 20
        matched = "region"

    else:
        # Foreign country or completely unknown city
        score   = 30
        matched = "novel"
    logger.info(f"location_score={score}, matched={matched}")
    return {**state, "location_score": score, "location_matched": matched}