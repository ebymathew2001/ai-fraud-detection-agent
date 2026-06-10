"""
agent/nodes/search_patterns.py
================================
NODE 5 — search_patterns

Reads:   transaction, avg_spend, location_matched, customer["home_city"]
Writes:  fraud_patterns (list[str]), pattern_score

What it does:
  1. Build a plain-English query string from transaction context.
  2. Embed it with nomic-embed-text (task_type="search_query").
  3. Query ChromaDB fraud_patterns collection → top 3 matches.
  4. pattern_score = len(matches) * 5, max 15.
"""

import os
import chromadb
from dotenv import load_dotenv
from agent.state import AgentState

load_dotenv()

CHROMA_PATH   = os.getenv("CHROMA_PATH", "./chroma_store")
NOMIC_API_KEY = os.getenv("NOMIC_API_KEY")


def _get_chroma_collection() -> chromadb.Collection:
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    return client.get_collection("fraud_patterns")


def _embed_query(text: str) -> list[float]:
    import ollama
    response = ollama.embed(
        model="nomic-embed-text",
        input=text,
    )
    return response["embeddings"][0]


def search_patterns(state: AgentState) -> AgentState:
    txn              = state["transaction"]
    avg_spend        = state["avg_spend"]
    location_matched = state["location_matched"]
    home_city        = state["customer"]["home_city"]

    # Build a natural language query — the same format the LLM would think in
    query = (
        f"Rs.{txn['amount']:.0f} {txn['merchant_category']} purchase "
        f"at {txn['merchant_name']} in {txn['transaction_location']}, "
        f"customer average spend Rs.{avg_spend:.0f}, "
        f"location match type: {location_matched}, "
        f"customer home city: {home_city}"
    )

    query_embedding = _embed_query(query)

    collection = _get_chroma_collection()
    results    = collection.query(
        query_embeddings=[query_embedding],
        n_results=3,
        include=["documents", "metadatas", "distances"],
    )

    fraud_patterns = results["documents"][0] if results["documents"] else []
    pattern_score  = min(len(fraud_patterns) * 5, 15)

    return {**state, "fraud_patterns": fraud_patterns, "pattern_score": pattern_score}