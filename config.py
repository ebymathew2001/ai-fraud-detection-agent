import os
from dotenv import load_dotenv

load_dotenv()

# ── API Keys ──────────────────────────────────────────────────
GROQ_API_KEY  = os.getenv("GROQ_API_KEY", "")

# ── Database ──────────────────────────────────────────────────
DATABASE_URL  = os.getenv("DATABASE_URL", "fraud.db")

# ── ChromaDB ──────────────────────────────────────────────────
CHROMA_PATH       = os.getenv("CHROMA_PATH", "./chroma_store")
CHROMA_COLLECTION = "fraud_patterns"

# ── Models ────────────────────────────────────────────────────
LLM_MODEL       = "llama-3.3-70b-versatile"
EMBED_MODEL     = "nomic-embed-text"
LLM_TEMPERATURE = 0.3
LLM_MAX_TOKENS  = 800