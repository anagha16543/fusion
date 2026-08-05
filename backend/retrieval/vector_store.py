"""
LexFusion ΓÇö ChromaDB In-Memory Vector Store
=============================================
Uses chromadb 0.4.x Client() (in-memory, no disk I/O).
Self-healing: reinitialises on stale-connection errors.
"""

from __future__ import annotations

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

COLLECTION_NAME = "lexfusion_legal_docs"


def _silence_telemetry():
    """
    Patch the broken posthog capture() in chromadb's telemetry so it no
    longer spams the console with 'takes 1 positional argument but 3 were given'.
    """
    try:
        import chromadb.telemetry.product.posthog as _ph
        _ph.Posthog.capture = lambda self, *a, **kw: None  # no-op
    except Exception:
        pass


class LexFusionVectorStore:
    """
    ChromaDB in-memory vector store for LexFusion legal document chunks.
    Self-healing: reinitialises the client if the connection goes stale.
    """

    def __init__(self):
        try:
            import chromadb                     # noqa: F401
            from langchain_chroma import Chroma  # noqa: F401
        except ImportError as exc:
            raise ImportError(
                "chromadb and langchain-chroma are required. "
                "Install with: pip install 'chromadb==0.4.24' langchain-chroma"
            ) from exc

        from backend.retrieval.embed import get_embeddings
        self._embeddings = get_embeddings()
        _silence_telemetry()
        self._init_store()
        logger.info("LexFusionVectorStore: ready.")

    def _init_store(self):
        """(Re-)create the ChromaDB client and Chroma store from scratch."""
        import chromadb
        from langchain_chroma import Chroma

        _silence_telemetry()

        # chromadb.Client() = pure in-memory, no disk, no server process.
        # This is the stable 0.4.x API (EphemeralClient in 0.5.x is broken).
        self._chroma_client = chromadb.Client()
        # Pre-create the collection so the schema is ready before LangChain touches it
        self._chroma_client.get_or_create_collection(COLLECTION_NAME)

        self._store = Chroma(
            client=self._chroma_client,
            collection_name=COLLECTION_NAME,
            embedding_function=self._embeddings,
        )
        logger.info("LexFusionVectorStore: ChromaDB initialised (collection=%s).", COLLECTION_NAME)

    # ΓöÇΓöÇ Write ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

    def add_documents(self, docs: list) -> int:
        if not docs:
            return 0
        try:
            self._store.add_documents(docs)
        except Exception as exc:
            logger.warning("add_documents failed (%s) ΓÇö reinitialising and retrying.", exc)
            self._init_store()
            self._store.add_documents(docs)  # let this raise if still broken

        count = len(docs)
        logger.info("LexFusionVectorStore: added %d chunks.", count)
        return count

    # ΓöÇΓöÇ Read ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

    def similarity_search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        try:
            results = self._store.similarity_search(query, k=k)
        except Exception as exc:
            logger.warning("similarity_search failed (%s) ΓÇö reinitialising.", exc)
            self._init_store()
            try:
                results = self._store.similarity_search(query, k=k)
            except Exception:
                return []

        return [
            {
                "source": doc.metadata.get("source", "Unknown"),
                "page":   doc.metadata.get("page", "?"),
                "chunk":  doc.page_content,
            }
            for doc in results
        ]

    def get_stats(self) -> Dict[str, Any]:
        try:
            count = self._store._collection.count()
        except Exception:
            count = 0
        return {
            "chunk_count": count,
            "collection":  COLLECTION_NAME,
            "status":      "active" if count > 0 else "empty",
        }

    def clear(self):
        try:
            self._chroma_client.delete_collection(COLLECTION_NAME)
            self._init_store()
            logger.info("LexFusionVectorStore: cleared.")
        except Exception as exc:
            logger.error("LexFusionVectorStore: clear failed ΓÇö %s", exc)

    def is_empty(self) -> bool:
        return self.get_stats()["chunk_count"] == 0
