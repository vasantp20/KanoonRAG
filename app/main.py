"""
KanoonRAG — FastAPI Application Entry Point

Configures CORS, lifespan (DB init/close), and includes all route modules.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import init_db, close_db
from app.api.routes import auth, clients, cases, query, documents, kanoon


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DB on startup, dispose on shutdown."""
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title="KanoonRAG API",
    description="Legal RAG system for Indian matrimonial disputes",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(clients.router)
app.include_router(cases.router)
app.include_router(query.router)
app.include_router(documents.router)
app.include_router(kanoon.router)


@app.get("/")
def root():
    return {"message": "Welcome to KanoonRAG API"}
