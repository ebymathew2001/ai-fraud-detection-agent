"""
agent/state.py
==============
Defines AgentState — the single shared object that flows
through every node in the LangGraph pipeline.

Every key a node reads or writes MUST be declared here.
"""

from typing import TypedDict


class AgentState(TypedDict, total=False):
    # ── INPUT ────────────────────────────────────────────────────
    transaction_id: str                  # provided by FastAPI

    # ── AFTER load_context ───────────────────────────────────────
    transaction: dict                    # full row from transactions table
    customer: dict                       # full row from customers table
    history: list[dict]                  # last 20 NORMAL txns for customer
    avg_spend: float                     # mean amount of history
    common_locations: list[str]          # top-3 locations from history
    common_categories: list[str]         # top-3 merchant categories from history
    last_known_location: str             # most recent txn location (or home_city)

    # ── AFTER analyze_amount ─────────────────────────────────────
    amount_score: int                    # 0 / 15 / 25 / 40

    # ── AFTER analyze_location ───────────────────────────────────
    location_score: int                  # 0 / 10 / 20 / 30
    location_matched: str                # "last_known" | "common" | "region" | "novel"

    # ── AFTER analyze_merchant ───────────────────────────────────
    merchant_score: int                  # 0-15

    # ── AFTER search_patterns ────────────────────────────────────
    fraud_patterns: list[str]            # top-3 matched descriptions from ChromaDB
    pattern_score: int                   # len(fraud_patterns) * 5, max 15

    # ── AFTER compute_risk_and_action ────────────────────────────
    risk_score: int                      # sum of all sub-scores (max 100)
    risk_level: str                      # LOW | MEDIUM | HIGH | CRITICAL
    recommendation: str                  # ALLOW | SEND_OTP | ESCALATE | BLOCK_CARD

    # ── AFTER generate_report ─────────────────────────────────────
    report: dict                         # full structured JSON report

    # ── AFTER save_investigation ──────────────────────────────────
    investigation_id: str                # UUID of the saved row