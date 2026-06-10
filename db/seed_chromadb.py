"""
db/seed_chromadb.py
===================
RUN THIS SECOND:  python db/seed_chromadb.py

Embeds 15 expert-written fraud pattern descriptions
into ChromaDB using nomic-embed-text.
Only needs to run ONCE — embeddings are persisted to ./chroma_store
"""

import os
import chromadb
import ollama
from dotenv import load_dotenv

load_dotenv()

CHROMA_PATH   = os.getenv("CHROMA_PATH", "./chroma_store")


# ── 15 plain-English fraud pattern descriptions ──────────────────────────────
FRAUD_PATTERNS = [
    {
        "id":       "pattern_1",
        "text":     "Transactions exceeding 10x the customer's average spend are a strong indicator of account compromise or card theft. Fraudsters often make one large purchase before the card is blocked.",
        "category": "amount_anomaly",
        "severity": "critical",
    },
    {
        "id":       "pattern_2",
        "text":     "High-value purchases at jewelry or electronics stores from a location the customer has never visited before frequently appear in fraud cases involving stolen card details.",
        "category": "location_merchant",
        "severity": "high",
    },
    {
        "id":       "pattern_3",
        "text":     "Multiple transactions originating from cities that are geographically distant within a 24-hour window is a strong account takeover signal, as a person cannot physically be in two places.",
        "category": "velocity",
        "severity": "critical",
    },
    {
        "id":       "pattern_4",
        "text":     "Large purchases of gift cards or cryptocurrency are disproportionately present in social engineering and phishing fraud, where victims are instructed to buy gift cards to pay fake debts or authorities.",
        "category": "merchant_category",
        "severity": "high",
    },
    {
        "id":       "pattern_5",
        "text":     "A transaction in a foreign country combined with a merchant category the customer has never used before is a high-risk combined signal suggesting the card was skimmed or data was stolen.",
        "category": "location_merchant",
        "severity": "high",
    },
    {
        "id":       "pattern_6",
        "text":     "Transactions between midnight and 4 AM local time at the cardholder's home city are unusual for most retail customers and can indicate unauthorized use while the cardholder is asleep.",
        "category": "time_anomaly",
        "severity": "medium",
    },
    {
        "id":       "pattern_7",
        "text":     "Wire transfers or forex transactions initiated from a retail banking account, especially for amounts exceeding 5x the customer's average, are a major red flag for business email compromise or romance scams.",
        "category": "merchant_category",
        "severity": "critical",
    },
    {
        "id":       "pattern_8",
        "text":     "Spending at a merchant category that accounts for 0% of the customer's transaction history for the past 6 months, combined with an above-average transaction amount, significantly elevates fraud risk.",
        "category": "behavioral_anomaly",
        "severity": "medium",
    },
    {
        "id":       "pattern_9",
        "text":     "A customer who typically makes domestic transactions suddenly initiates a high-value international transaction without prior travel bookings or gradual international spending history is a common card fraud pattern.",
        "category": "location_anomaly",
        "severity": "high",
    },
    {
        "id":       "pattern_10",
        "text":     "Rapid succession of small test transactions followed immediately by a large transaction is a card-testing pattern where fraudsters validate a stolen card with micro-purchases before making the main fraudulent purchase.",
        "category": "velocity",
        "severity": "high",
    },
    {
        "id":       "pattern_11",
        "text":     "Electronics purchases in Southeast Asian or Middle Eastern cities for amounts that are 5x or more above the customer's average are among the most common patterns in international card fraud and skimming operations.",
        "category": "location_merchant",
        "severity": "critical",
    },
    {
        "id":       "pattern_12",
        "text":     "A single high-value crypto exchange or cryptocurrency purchase from an account with no prior crypto activity, especially from an unfamiliar location, is strongly correlated with account takeover by financially motivated threat actors.",
        "category": "merchant_category",
        "severity": "critical",
    },
    {
        "id":       "pattern_13",
        "text":     "Jewelry purchases at unfamiliar merchants outside the customer's home region, particularly when the transaction amount exceeds the customer's 90th percentile spend, are a well-documented fraud indicator in retail banking.",
        "category": "merchant_category",
        "severity": "high",
    },
    {
        "id":       "pattern_14",
        "text":     "When a customer's last transaction was in one country and the next transaction occurs in a different country within a few hours making physical travel implausible, this impossible travel pattern is a definitive fraud signal.",
        "category": "velocity",
        "severity": "critical",
    },
    {
        "id":       "pattern_15",
        "text":     "First-time transactions at luxury goods merchants such as high-end jewelry, designer goods, or premium electronics in combination with an unusually large transaction amount and a new geographic location represent a convergence of three independent fraud risk factors.",
        "category": "combined_signal",
        "severity": "critical",
    },
]


def get_chroma_client() -> chromadb.PersistentClient:
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    return client


def get_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings locally using Ollama.
    Returns a list of float vectors.
    """

    embeddings = []

    for text in texts:
        response = ollama.embed(
            model="nomic-embed-text",
            input=text,
        )

        embeddings.append(response["embeddings"][0])

    return embeddings


def seed_patterns(client: chromadb.PersistentClient):
    # Delete existing collection if it exists (clean re-seed)
    try:
        client.delete_collection("fraud_patterns")
        print("  Deleted existing fraud_patterns collection.")
    except Exception:
        pass

    collection = client.create_collection(
        name="fraud_patterns",
        metadata={"hnsw:space": "cosine"},
    )

    texts     = [p["text"]     for p in FRAUD_PATTERNS]
    ids       = [p["id"]       for p in FRAUD_PATTERNS]
    metadatas = [{"category": p["category"], "severity": p["severity"]} for p in FRAUD_PATTERNS]

    print(" Generating embeddings via Ollama (this may take a few seconds) ...")
    embeddings = get_embeddings(texts)

    collection.add(
        ids=ids,
        documents=texts,
        metadatas=metadatas,
        embeddings=embeddings,
    )

    print(f" Seeded {len(FRAUD_PATTERNS)} fraud patterns into ChromaDB.")
    print(f"   Stored at: {CHROMA_PATH}")
    return collection


def main():
    print(" Seeding ChromaDB fraud patterns ...")
    client = get_chroma_client()
    seed_patterns(client)
    print(" ChromaDB seeding complete.")


if __name__ == "__main__":
    main()