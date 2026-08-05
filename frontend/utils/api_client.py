"""
LexFusion Frontend API Client
==============================
Communicates with the FastAPI backend if available (local server mode).
If the backend is offline, falls back to Local Direct Mode ΓÇö running the
full RAG pipeline and LangGraph agents directly in-process.

This is the primary execution path on Streamlit Cloud, where no
separate backend server is running.
"""

from __future__ import annotations

import os
import sys
import logging
import requests
from typing import Any, Optional

# Add project root to path for local imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

logger = logging.getLogger(__name__)

# Backend API configuration
API_BASE_URL = os.getenv("LEXFUSION_API_URL", "http://localhost:8000")

# ΓöÇΓöÇ Try importing agents (LangGraph debate pipeline) ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

try:
    from agents.generate import generate_answer, run_debate
    LOCAL_AGENTS_AVAILABLE = True
except ImportError:
    LOCAL_AGENTS_AVAILABLE = False
    logger.warning("agents package not importable ΓÇö local agent mode unavailable.")

# ΓöÇΓöÇ Try importing backend RAG pipeline ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

try:
    from backend import ingest_pdf as _backend_ingest, search_documents as _backend_search
    from backend.retrieval.vector_store import LexFusionVectorStore
    LOCAL_BACKEND_AVAILABLE = True
except ImportError:
    LOCAL_BACKEND_AVAILABLE = False
    logger.warning("backend package not importable ΓÇö RAG pipeline unavailable.")


class LexFusionAPIClient:
    """
    Smart API client for LexFusion.

    Priority:
        1. FastAPI backend server (if running locally on port 8000)
        2. Local Direct Mode: full in-process RAG pipeline + agents
    """

    def __init__(self):
        self.api_url = API_BASE_URL
        self.local_mode = not self._check_backend_online()

        # Initialize in-process vector store for local/cloud mode
        self.vector_store: Optional[Any] = None
        if LOCAL_BACKEND_AVAILABLE:
            try:
                self.vector_store = LexFusionVectorStore()
                logger.info("LexFusionAPIClient: In-memory vector store initialized.")
            except Exception as exc:
                logger.error("LexFusionAPIClient: Failed to initialize vector store ΓÇö %s", exc)

        if self.local_mode:
            logger.info("LexFusion: Running in LOCAL DIRECT mode (Streamlit Cloud compatible).")
        else:
            logger.info("LexFusion: FastAPI backend detected ΓÇö running in API mode.")

    def _ensure_vector_store(self):
        """
        Return a healthy vector store, re-creating it if the underlying
        ChromaDB connection has gone stale (e.g. after Streamlit hot-reload).
        """
        if not LOCAL_BACKEND_AVAILABLE:
            return None
        if self.vector_store is None:
            try:
                self.vector_store = LexFusionVectorStore()
            except Exception as exc:
                logger.error("_ensure_vector_store: could not create store ΓÇö %s", exc)
                return None
        # Quick health-check: if stats throws, reinit
        try:
            self.vector_store.get_stats()
        except Exception as exc:
            logger.warning("Vector store unhealthy (%s) ΓÇö reinitialising.", exc)
            try:
                self.vector_store = LexFusionVectorStore()
            except Exception as exc2:
                logger.error("Reinit failed ΓÇö %s", exc2)
                self.vector_store = None
        return self.vector_store

    def _check_backend_online(self) -> bool:
        """Sends a lightweight health check request to the FastAPI backend."""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=1.5)
            return response.status_code == 200
        except requests.RequestException:
            return False

    # ΓöÇΓöÇ Document Ingestion ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

    def upload_document(self, file_name: str, file_content: bytes) -> dict[str, Any]:
        """
        Ingest a PDF document into the vector store.

        In API mode: POSTs to /upload.
        In local mode: runs the full extract ΓåÆ chunk ΓåÆ embed ΓåÆ index pipeline.
        """
        # Try API mode first
        if not self.local_mode:
            try:
                files = {"file": (file_name, file_content, "application/pdf")}
                response = requests.post(f"{self.api_url}/upload", files=files, timeout=60)
                if response.status_code == 200:
                    return response.json()
                logger.warning("API upload failed (status %s) ΓÇö falling back to local.", response.status_code)
            except requests.RequestException as err:
                logger.warning("API upload request failed: %s ΓÇö falling back to local.", err)

        # Local direct mode: run ingestion pipeline in-process
        if LOCAL_BACKEND_AVAILABLE and self._ensure_vector_store() is not None:
            return _backend_ingest(self._ensure_vector_store(), file_content, file_name)

        # Absolute fallback (shouldn't happen in normal deployment)
        return {
            "status": "success",
            "filename": file_name,
            "message": f"Ingested {file_name} (mock ΓÇö backend unavailable).",
        }

    def get_stats(self) -> dict[str, Any]:
        """Return vector store statistics (chunk count, status)."""
        if not self.local_mode:
            try:
                response = requests.get(f"{self.api_url}/stats", timeout=3)
                if response.status_code == 200:
                    return response.json()
            except requests.RequestException:
                pass

        if self._ensure_vector_store() is not None:
            return self._ensure_vector_store().get_stats()

        return {"chunk_count": 0, "status": "empty"}

    # ΓöÇΓöÇ Query / Debate ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

    def query(
        self,
        query: str,
        debate_mode: bool = True,
        top_k: int = 5,
        max_rounds: Optional[int] = None,
        language: str = "English",
    ) -> dict[str, Any]:
        """
        Run a legal query ΓÇö either single-shot RAG or full Cross-Examine debate.

        Args:
            query:       Legal question from the user.
            debate_mode: True = full adversarial debate; False = single-shot RAG.
            top_k:       Number of document chunks to retrieve.
            max_rounds:  Override for debate rounds.
            language:    Response language for all AI agents.

        Returns:
            Dict matching GenerateResponse or DebateResponse model structure.
        """
        # ΓöÇΓöÇ API Mode ΓöÇΓöÇ
        if not self.local_mode:
            try:
                payload: dict[str, Any] = {
                    "query": query,
                    "debate_mode": debate_mode,
                    "top_k": top_k,
                    "language": language,
                }
                if max_rounds is not None:
                    payload["max_rounds"] = max_rounds

                response = requests.post(
                    f"{self.api_url}/query", json=payload, timeout=120
                )
                if response.status_code == 200:
                    return response.json()
                logger.warning(
                    "API query failed (status %s) ΓÇö falling back to local.",
                    response.status_code,
                )
            except requests.RequestException as err:
                logger.warning("API query failed: %s ΓÇö falling back to local.", err)

        # ΓöÇΓöÇ Local Direct Mode ΓöÇΓöÇ
        if not LOCAL_AGENTS_AVAILABLE:
            return {
                "status": "error",
                "error_message": (
                    "Both backend API and local agents are unavailable. "
                    "Please install requirements: pip install -r requirements.txt"
                ),
            }

        # Retrieve context from vector store (or use mock fallback)
        if LOCAL_BACKEND_AVAILABLE and self._ensure_vector_store() is not None:
            sources, context = _backend_search(self._ensure_vector_store(), query, k=top_k)
        else:
            sources, context = self._get_mock_context_fallback()

        try:
            if debate_mode:
                res = run_debate(
                    query=query,
                    context=context,
                    source_documents=sources,
                    max_rounds=max_rounds,
                    language=language,
                )
            else:
                res = generate_answer(
                    query=query,
                    context=context,
                    source_documents=sources,
                    language=language,
                )
            return res.model_dump()

        except Exception as exc:
            logger.error("Local agent execution failed: %s", exc)
            return {
                "status": "error",
                "error_message": f"Agent execution failed: {exc}",
            }

    def _get_mock_context_fallback(self):
        """Fallback mock context when no PDFs are uploaded and backend unavailable."""
        sources = [
            {
                "source": "sample_contract.pdf",
                "page": 4,
                "chunk": "Section 14.1 Indemnification: The vendor shall indemnify and hold harmless the client from any third-party claims arising out of the Services.",
            },
            {
                "source": "sample_terms.pdf",
                "page": 2,
                "chunk": "Section 8.2 Limitation of Liability: Neither party shall be liable for consequential, indirect, or punitive damages.",
            },
        ]
        context = "\n\n".join(f"[Source: {s['source']}, Page {s['page']}]\n{s['chunk']}" for s in sources)
        return sources, context
