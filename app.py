"""
app.py
======
FastAPI entry point.

RUN THIS THIRD (after init_db.py and seed_chromadb.py):
  python app.py

Dashboard →  http://localhost:8000
API docs  →  http://localhost:8000/docs
"""

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv

from api.routes import router

load_dotenv()

app = FastAPI(
    title="Fraud Detection API",
    description="AI-Powered Banking Fraud Detection — LangGraph + Groq + ChromaDB",
    version="1.0.0",
)

# All API routes
app.include_router(router)

# Serve dashboard HTML at root
@app.get("/", include_in_schema=False)
def serve_dashboard():
    return FileResponse("static/index.html")

# Mount static folder (for future CSS/JS files)
app.mount("/static", StaticFiles(directory="static"), name="static")


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)