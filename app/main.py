from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.db.session import init_db
from app.db.checkpointer import init_checkpointer
from app.api.routes import router

app = FastAPI(title="Agentic Assortment & Promotion Decision Engine", version="1.0.0")
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

@app.on_event("startup")
def startup():
    init_db()
    init_checkpointer()

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(router)
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
