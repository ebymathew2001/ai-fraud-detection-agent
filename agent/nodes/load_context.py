"""
agent/nodes/load_context.py
============================
NODE 1 — load_context

Reads:   state["transaction_id"]
Writes:  transaction, customer, history,
         avg_spend, common_locations, common_categories, last_known_location

What it does:
  1. Fetch the suspicious transaction row from SQLite.
  2. Fetch the customer row.
  3. Fetch the last 20 NORMAL transactions for that customer.
  4. Compute avg_spend, top-3 common_locations, top-3 common_categories.
  5. Set last_known_location = most recent NORMAL txn location,
     fallback to home_city if the customer has no history.
"""


import sqlite3
from collections import Counter
from agent.state import AgentState
from config import DATABASE_URL



def _get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def load_context(state: AgentState) -> AgentState:
    txn_id = state["transaction_id"]
    conn   = _get_db()

    # 1. Fetch the suspicious transaction
    txn_row = conn.execute(
        "SELECT * FROM transactions WHERE txn_id = ?", (txn_id,)
    ).fetchone()

    if not txn_row:
        conn.close()
        raise ValueError(f"Transaction '{txn_id}' not found in database.")

    transaction = dict(txn_row)

    # 2. Fetch customer
    customer_row = conn.execute(
        "SELECT * FROM customers WHERE customer_id = ?",
        (transaction["customer_id"],)
    ).fetchone()
    customer = dict(customer_row)

    # 3. Fetch last 20 NORMAL transactions (most recent first)
    history_rows = conn.execute(
        """SELECT * FROM transactions
           WHERE customer_id = ? AND status = 'NORMAL'
           ORDER BY timestamp DESC LIMIT 20""",
        (transaction["customer_id"],)
    ).fetchall()
    conn.close()

    history = [dict(row) for row in history_rows]

    # 4. Compute avg_spend
    avg_spend = (
        sum(h["amount"] for h in history) / len(history)
        if history else transaction["amount"]
    )

    # 5. Top-3 locations and categories
    location_counts   = Counter(h["transaction_location"] for h in history)
    common_locations  = [loc for loc, _ in location_counts.most_common(3)]

    category_counts   = Counter(h["merchant_category"] for h in history)
    common_categories = [cat for cat, _ in category_counts.most_common(3)]

    # 6. Last known location (fallback to home_city)
    last_known_location = (
        history[0]["transaction_location"]
        if history else customer["home_city"]
    )

    return {
        **state,
        "transaction":          transaction,
        "customer":             customer,
        "history":              history,
        "avg_spend":            round(avg_spend, 2),
        "common_locations":     common_locations,
        "common_categories":    common_categories,
        "last_known_location":  last_known_location,
    }