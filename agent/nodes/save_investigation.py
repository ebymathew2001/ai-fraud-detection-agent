"""
agent/nodes/save_investigation.py
===================================
NODE 8 — save_investigation

Reads:   state["report"]
Writes:  investigations table in SQLite, state["investigation_id"]

Kept deliberately separate from generate_report so that:
  - LLM timeouts and DB failures fail independently.
  - You can swap the storage backend without touching the LLM node.
"""

import os
import json
import sqlite3
from dotenv import load_dotenv
from agent.state import AgentState

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "fraud.db")


def _get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def save_investigation(state: AgentState) -> AgentState:
    report = state["report"]
    conn   = _get_db()

    conn.execute(
        """INSERT INTO investigations
           (investigation_id, txn_id, risk_score, risk_level,
            recommendation, reasons, report, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            report["investigation_id"],
            report["txn_id"],
            report["risk_score"],
            report["risk_level"],
            report["recommendation"],
            json.dumps(report["reasons"]),  # stored as JSON string
            json.dumps(report),             # full blob for GET /investigations/{id}
            report["created_at"],
        )
    )
    conn.commit()
    conn.close()

    return {**state, "investigation_id": report["investigation_id"]}