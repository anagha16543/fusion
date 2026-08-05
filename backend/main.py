"""
LexFusion — FastAPI Backend Server (Optional)
==============================================
Run this for local server deployment:
    uvicorn backend.main:app --reload --port 8000

For Streamlit Cloud deployment, this is NOT required.
The frontend's api_client.py runs in local mode, calling agents directly.
"""

from __future__ import annotations

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from backend import ingest_pdf, search_documents
from backend.retrieval.vector_store import LexFusionVectorStore
from backend.schemas.models import HealthResponse, UploadResponse, StatsResponse, QueryRequest

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Shared vector store instance for server lifetime
_vector_store: LexFusionVectorStore | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _vector_store
    logger.info("LexFusion API: Starting up — initializing vector store...")
    _vector_store = LexFusionVectorStore()
    logger.info("LexFusion API: Vector store ready.")
    yield
    logger.info("LexFusion API: Shutting down.")


app = FastAPI(
    title="LexFusion API",
    description="Legal RAG backend with adversarial debate graph",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow Streamlit frontend (port 8501) and any localhost origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Lightweight health check used by frontend's check_backend_online()."""
    return HealthResponse()


@app.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Ingest a PDF: extract → chunk → embed → index into ChromaDB.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    result = ingest_pdf(_vector_store, file_bytes, file.filename)

    if result.get("status") == "error":
        raise HTTPException(status_code=422, detail=result.get("message", "Ingestion failed."))

    # Build UploadResponse explicitly to avoid Pydantic rejecting extra keys
    # that ingest_pdf() may include (e.g. extra debug fields) and to guarantee
    # every required field is present even when the dict is sparse.
    return UploadResponse(
        status=result.get("status", "success"),
        filename=result.get("filename", file.filename),
        pages_extracted=result.get("pages_extracted", 0),
        chunks_added=result.get("chunks_added", 0),
        message=result.get("message", ""),
    )


@app.post("/query")
async def query_endpoint(request: QueryRequest):
    """
    Run a legal query against indexed documents.
    Returns either a single-shot answer or full debate response.
    """
    from agents.generate import generate_answer, run_debate

    # Retrieve relevant context from vector store
    sources, context = search_documents(_vector_store, request.query, k=request.top_k)

    try:
        if request.debate_mode:
            result = run_debate(
                query=request.query,
                context=context,
                source_documents=sources,
                max_rounds=request.max_rounds,
                language=request.language,
            )
        else:
            result = generate_answer(
                query=request.query,
                context=context,
                source_documents=sources,
                language=request.language,
            )
        return result.model_dump()
    except Exception as exc:
        logger.error("/query: Agent execution failed — %s", exc)
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {exc}")


@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Return current vector store statistics."""
    if _vector_store is None:
        return StatsResponse()
    stats = _vector_store.get_stats()
    return StatsResponse(**stats)
