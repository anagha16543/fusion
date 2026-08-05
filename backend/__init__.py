"""
LexFusion ΓÇö Backend Public API
================================
Clean public interface used by frontend/utils/api_client.py in local mode.
Orchestrates the full ingestion and retrieval pipeline.
"""

from __future__ import annotations

import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)


def ingest_pdf(
    vector_store,
    file_bytes: bytes,
    filename: str,
) -> Dict[str, Any]:
    """
    Run the full ingestion pipeline: extract ΓåÆ chunk ΓåÆ embed ΓåÆ index.

    Args:
        vector_store: LexFusionVectorStore instance (from session state).
        file_bytes:   Raw bytes of the uploaded PDF.
        filename:     Original filename for metadata.

    Returns:
        Dict with status, pages_extracted, chunks_added, message.
    """
    from backend.ingestion.extract import extract_text_from_pdf
    from backend.ingestion.chunk import chunk_documents

    try:
        # Step 1: Extract text from PDF
        pages = extract_text_from_pdf(file_bytes, filename)
        logger.info("ingest_pdf: Extracted %d pages from '%s'.", len(pages), filename)

        # Step 2: Chunk the extracted text
        docs = chunk_documents(pages)
        logger.info("ingest_pdf: Created %d chunks.", len(docs))

        # Step 3: Embed + index into vector store
        count = vector_store.add_documents(docs)

        return {
            "status": "success",
            "filename": filename,
            "pages_extracted": len(pages),
            "chunks_added": count,
            "message": f"Successfully ingested '{filename}': {len(pages)} pages ΓåÆ {count} chunks indexed.",
        }

    except RuntimeError as exc:
        logger.error("ingest_pdf: %s", exc)
        return {"status": "error", "filename": filename, "message": str(exc)}
    except Exception as exc:
        logger.error("ingest_pdf: Unexpected error ΓÇö %s", exc)
        return {"status": "error", "filename": filename, "message": f"Ingestion failed: {exc}"}


def search_documents(
    vector_store,
    query: str,
    k: int = 5,
) -> Tuple[List[Dict[str, Any]], str]:
    """
    Retrieve the top-k most relevant document chunks for a query.

    Args:
        vector_store: LexFusionVectorStore instance.
        query:        User's legal question.
        k:            Number of chunks to retrieve.

    Returns:
        Tuple of (source_documents list, formatted context string).
    """
    if vector_store is None or vector_store.is_empty():
        logger.warning("search_documents: Vector store is empty ΓÇö returning mock context.")
        return _get_mock_sources(), _get_mock_context()

    sources = vector_store.similarity_search(query, k=k)

    if not sources:
        logger.warning("search_documents: No results found ΓÇö returning mock context.")
        return _get_mock_sources(), _get_mock_context()

    # Format context string for LLM consumption
    context_parts = []
    for i, src in enumerate(sources, 1):
        context_parts.append(
            f"[Document {i} ΓÇö Source: {src['source']}, Page {src['page']}]\n{src['chunk']}"
        )
    context = "\n\n---\n\n".join(context_parts)

    return sources, context


# ΓöÇΓöÇ Fallback mock context (used when no PDFs have been uploaded) ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

def _get_mock_sources() -> List[Dict[str, Any]]:
    return [
        {
            "source": "contract_agreement_v2.pdf",
            "page": 4,
            "chunk": "Section 14.1 Indemnification: The vendor shall indemnify and hold harmless the client from any third-party claims arising out of the Services.",
        },
        {
            "source": "terms_and_conditions.pdf",
            "page": 2,
            "chunk": "Section 8.2 Limitation of Liability: Neither party shall be liable for consequential, indirect, or punitive damages.",
        },
    ]


def _get_mock_context() -> str:
    return (
        "Section 14.1 INDEMNIFICATION. The Vendor shall indemnify, defend, and hold harmless the "
        "Client and its officers, directors, employees, and agents from any third-party claims "
        "alleging that the Services infringe any patent, copyright, trademark, or trade secret.\n\n"
        "Section 8.2 LIMITATION OF LIABILITY. In no event shall either party be liable for any "
        "indirect, incidental, special, punitive, or consequential damages, including loss of profits.\n\n"
        "Section 12.4 TERMINATION FOR CAUSE. Either party may terminate this Agreement immediately "
        "upon written notice if the other party breaches any material provision and fails to cure "
        "such breach within thirty (30) days after receipt of written notice."
    )
