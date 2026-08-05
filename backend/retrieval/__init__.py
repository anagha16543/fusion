# backend/retrieval — Vector store and embedding sub-package
from backend.retrieval.embed import get_embeddings
from backend.retrieval.vector_store import LexFusionVectorStore

__all__ = ["get_embeddings", "LexFusionVectorStore"]
