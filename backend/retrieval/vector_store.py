"""
LexFusion — ChromaDB In-Memory Vector Store
=============================================
Wraps a ChromaDB in-memory client with LangChain-Chroma integration.
In-memory means the store lives for the duration of the Streamlit session —
perfect for Streamlit Cloud where disk persistence is unreliable.

Usage:
    store = LexFusionVectorStore()
    store.add_documents(docs)           # List[LangChain Document]
    results = store.similarity_search(query, k=5)
    stats = store.get_stats()
    store.clear()
"""

from __future__ import annotations

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

COLLECTION_NAME = "lexfusion_legal_docs"


class LexFusionVectorStore:
    """
    ChromaDB in-memory vector store for LexFusion legal document chunks.

    Thread-safe for Streamlit's single-threaded session model.
    Each instantiation creates a fresh in-memory ChromaDB client.
    """

    def __init__(self):
        try:
            import chromadb
            from langchain_chroma import Chroma
        except ImportError as exc:
            raise ImportError(
                "chromadb and langchain-chroma are required. "
                "Install with: pip install chromadb langchain-chroma"
            ) from exc

        from backend.retrieval.embed import get_embeddings

        self._embeddings = get_embeddings()

        # Ephemeral in-memory client — no disk I/O, Streamlit Cloud safe
        self._chroma_client = chromadb.Client()

        self._store = Chroma(
            client=self._chroma_client,
            collection_name=COLLECTION_NAME,
            embedding_function=self._embeddings,
        )

        logger.info("LexFusionVectorStore: Initialized in-memory ChromaDB collection '%s'.", COLLECTION_NAME)

    # ── Write ──────────────────────────────────────────────────────────────────

    def add_documents(self, docs: list) -> int:
        """
        Embed and index a list of LangChain Documents into the vector store.

        Args:
            docs: List of LangChain Document objects (from chunk.py).

        Returns:
            Number of chunks successfully added.
        """
        if not docs:
            return 0

        self._store.add_documents(docs)
        count = len(docs)
        logger.info("LexFusionVectorStore: Added %d chunks to collection.", count)
        return count

    # ── Read ───────────────────────────────────────────────────────────────────

    def similarity_search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve the top-k most semantically relevant chunks for a query.

        Args:
            query: User's legal question (will be embedded).
            k:     Number of top results to return.

        Returns:
            List of dicts: [{"source": str, "page": int, "chunk": str}, ...]
        """
        try:
            results = self._store.similarity_search(query, k=k)
        except Exception as exc:
            logger.warning("similarity_search failed: %s — returning empty results.", exc)
            return []

        return [
            {
                "source": doc.metadata.get("source", "Unknown Document"),
                "page": doc.metadata.get("page", "?"),
                "chunk": doc.page_content,
            }
            for doc in results
        ]

    def get_stats(self) -> Dict[str, Any]:
        """Return current collection statistics."""
        try:
            count = self._store._collection.count()
        except Exception:
            count = 0
        return {
            "chunk_count": count,
            "collection": COLLECTION_NAME,
            "status": "active" if count > 0 else "empty",
        }

    # ── Admin ──────────────────────────────────────────────────────────────────

    def clear(self):
        """Drop and recreate the collection, wiping all indexed documents."""
        try:
            from langchain_chroma import Chroma
            self._chroma_client.delete_collection(COLLECTION_NAME)
            self._store = Chroma(
                client=self._chroma_client,
                collection_name=COLLECTION_NAME,
                embedding_function=self._embeddings,
            )
            logger.info("LexFusionVectorStore: Collection cleared.")
        except Exception as exc:
            logger.error("LexFusionVectorStore: Clear failed — %s", exc)

    def is_empty(self) -> bool:
        """Returns True if no documents have been indexed yet."""
        stats = self.get_stats()
        return stats["chunk_count"] == 0
