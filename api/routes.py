"""
api/routes.py
=============
All 4 REST endpoints:

  GET  /alerts                  — all SUSPICIOUS txns + customer name + investigated flag
  POST /investigations          — trigger investigation (or return cached)
  GET  /investigations/{txn_id} — fetch one saved investigation
  GET  /investigations          — summary list of all investigations
"""


import json
import sqlite3
import traceback
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from config import DATABASE_URL

from agent.graph import get_graph

# ── Logging ───────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("fraud.routes")




router = APIRouter()


def _get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


class InvestigationRequest(BaseModel):
    transaction_id: str


# ─────────────────────────────────────────────────────────────────────────────
# GET /alerts
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/alerts")
def get_alerts():
    """
    Returns all SUSPICIOUS transactions with customer name.
    The 'investigated' boolean is derived via LEFT JOIN — not a stored column.
    """
    logger.info("GET /alerts called")  
    conn = _get_db()
    rows = conn.execute("""
        SELECT
            t.txn_id,
            t.customer_id,
            c.name               AS customer_name,
            t.amount,
            t.merchant_name,
            t.merchant_category,
            t.transaction_location,
            t.timestamp,
            t.status,
            CASE WHEN i.txn_id IS NOT NULL THEN 1 ELSE 0 END AS investigated
        FROM transactions t
        JOIN     customers     c ON t.customer_id = c.customer_id
        LEFT JOIN investigations i ON t.txn_id    = i.txn_id
        WHERE t.status = 'SUSPICIOUS'
        ORDER BY t.timestamp DESC
    """).fetchall()
    conn.close()
    logger.info(f"GET /alerts returning {len(rows)} alerts")
    return [dict(row) for row in rows]


# ─────────────────────────────────────────────────────────────────────────────
# POST /investigations
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/investigations")
def create_investigation(body: InvestigationRequest):
    """
    Idempotency guard:
      1. Check investigations table for existing row with this txn_id.
      2. If found → return cached result with cached: true.
      3. If not   → run LangGraph pipeline, return report with cached: false.
    """
    txn_id = body.transaction_id
    logger.info(f"POST /investigations called with txn_id={txn_id}")
    conn   = _get_db()

    # Step 1 — idempotency check
    existing = conn.execute(
        "SELECT * FROM investigations WHERE txn_id = ?", (txn_id,)
    ).fetchone()
    conn.close()

    if existing:
        logger.info(f"Returning cached investigation for {txn_id}")
        result            = dict(existing)
        result["reasons"] = json.loads(result["reasons"])
        result["report"]  = json.loads(result["report"])
        result["cached"]  = True
        return result

    # Step 2 — confirm the transaction exists
    conn    = _get_db()
    txn_row = conn.execute(
        "SELECT * FROM transactions WHERE txn_id = ?", (txn_id,)
    ).fetchone()
    conn.close()

    if not txn_row:
        raise HTTPException(status_code=404, detail=f"Transaction '{txn_id}' not found.")

    # Step 3 — run the agent
    try:
        logger.info(f"Starting LangGraph pipeline for {txn_id}")
        result = get_graph().invoke({"transaction_id": txn_id})
        logger.info(f"Pipeline completed for {txn_id}")
    except Exception as e:
        logger.error(f"Pipeline failed for {txn_id}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Agent pipeline error: {str(e)}")

    report           = result["report"]
    report["cached"] = False
    return report


# ─────────────────────────────────────────────────────────────────────────────
# GET /investigations/{txn_id}
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/investigations/{txn_id}")
def get_investigation(txn_id: str):
    """Fetch one saved investigation. Returns 404 if not yet investigated."""
    logger.info(f"GET /investigations/{txn_id} called") 
    conn = _get_db()
    row  = conn.execute(
        "SELECT * FROM investigations WHERE txn_id = ?", (txn_id,)
    ).fetchone()
    conn.close()

    if not row:
        logger.warning(f"Investigation not found for {txn_id}")
        raise HTTPException(
            status_code=404,
            detail=f"No investigation found for '{txn_id}'. Run POST /investigations first."
        )
    logger.info(f"Returning investigation for {txn_id}")
    result            = dict(row)
    result["reasons"] = json.loads(result["reasons"])
    result["report"]  = json.loads(result["report"])
    return result


# ─────────────────────────────────────────────────────────────────────────────
# GET /investigations
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/investigations")
def list_investigations():
    """Summary list of all investigations — no full report blob."""
    logger.info("GET /investigations called")
    conn = _get_db()
    rows = conn.execute("""
        SELECT
            i.investigation_id,
            i.txn_id,
            c.name               AS customer_name,
            t.amount,
            t.merchant_category,
            t.transaction_location,
            i.risk_score,
            i.risk_level,
            i.recommendation,
            i.reasons,
            i.created_at
        FROM investigations i
        JOIN transactions t ON i.txn_id      = t.txn_id
        JOIN customers    c ON t.customer_id = c.customer_id
        ORDER BY i.created_at DESC
    """).fetchall()
    conn.close()

    results = []
    for row in rows:
        item            = dict(row)
        item["reasons"] = json.loads(item["reasons"])
        results.append(item)
        
    return results