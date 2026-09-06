"""
KanoonRAG — FastAPI Application Entry Point

Configures CORS, lifespan (DB init/close), and includes all route modules.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import init_db, close_db
from app.api.routes import auth, query


from app.core.vector_store import VectorStore
from app.core.llm_provider import LLMProvider
from app.core.embeddings import EmbeddingService
from app.core.rag_engine.engine import RAGEngine

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DB on startup, dispose on shutdown."""
    await init_db()
    
    # Initialize ML and Vector resources
    vector_store = VectorStore()
    vector_store.initialize()
    
    llm_provider = LLMProvider()
    intent_llm = LLMProvider(provider="sarvam")
    embedding_service = EmbeddingService()
    
    app.state.vector_store = vector_store
    app.state.llm_provider = llm_provider
    app.state.intent_llm = intent_llm
    app.state.embedding_service = embedding_service
    app.state.rag_engine = RAGEngine(vector_store, llm_provider, intent_llm, embedding_service)
    
    
    yield
    

    
    await close_db()
    vector_store.close()
    await llm_provider.close()
    await intent_llm.close()


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
app.include_router(query.router)


@app.get("/")
def root():
    return {"message": "Welcome to KanoonRAG API"}
