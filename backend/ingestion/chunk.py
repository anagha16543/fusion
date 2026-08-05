"""
LexFusion — Document Chunker
==============================
Splits extracted page text into overlapping chunks using LangChain's
RecursiveCharacterTextSplitter with legal-document-optimized separators.
"""

from __future__ import annotations

import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

# Legal-document-aware separator order: paragraphs → sentences → clauses → words
LEGAL_SEPARATORS = ["\n\n", "\n", ". ", "; ", ", ", " ", ""]


def chunk_documents(
    pages: List[Dict],
    chunk_size: int = 800,
    overlap: int = 150,
) -> list:
    """
    Split extracted page text into overlapping chunks for vector indexing.

    Args:
        pages:       List of page dicts from extract_text_from_pdf().
        chunk_size:  Maximum characters per chunk (default 800 — good for legal text).
        overlap:     Overlap between consecutive chunks (default 150).

    Returns:
        List of LangChain Document objects with metadata {source, page, chunk_index}.

    Raises:
        ImportError: If langchain_text_splitters is not installed.
    """
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        from langchain_core.documents import Document
    except ImportError as exc:
        raise ImportError(
            "langchain and langchain_text_splitters are required for chunking. "
            "Install with: pip install langchain langchain-text-splitters"
        ) from exc

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=LEGAL_SEPARATORS,
        length_function=len,
        is_separator_regex=False,
    )

    all_chunks: list = []

    for page in pages:
        raw_chunks = splitter.create_documents(
            texts=[page["text"]],
            metadatas=[{
                "source": page["source"],
                "page": page["page"],
            }],
        )

        # Enrich each chunk with its index within the page for traceability
        for idx, chunk in enumerate(raw_chunks):
            chunk.metadata["chunk_index"] = idx
            all_chunks.append(chunk)

    logger.info(
        "chunk_documents: Split %d pages into %d chunks (size=%d, overlap=%d).",
        len(pages),
        len(all_chunks),
        chunk_size,
        overlap,
    )

    return all_chunks
