"""
LexFusion — PDF Text Extractor
================================
Uses PyMuPDF (fitz) to extract text page-by-page from uploaded PDF bytes.
Returns a list of page dicts ready for chunking.
"""

from __future__ import annotations

import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_bytes: bytes, filename: str = "document.pdf") -> List[Dict]:
    """
    Extract text from all pages of a PDF file given as raw bytes.

    Args:
        file_bytes: Raw PDF bytes from an uploaded file.
        filename:   Original filename (used as source metadata).

    Returns:
        List of dicts: [{"page": int, "text": str, "source": str}, ...]
        Empty pages (no extractable text) are skipped.

    Raises:
        RuntimeError: If PyMuPDF cannot open or parse the PDF.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError as exc:
        raise ImportError(
            "PyMuPDF is required for PDF extraction. "
            "Install it with: pip install pymupdf"
        ) from exc

    pages: List[Dict] = []

    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        total_pages = len(doc)
        logger.info("extract_text_from_pdf: Opened '%s' — %d pages.", filename, total_pages)

        for page_num in range(total_pages):
            page = doc[page_num]
            text = page.get_text("text").strip()

            # Skip pages with no extractable text (scanned images without OCR, etc.)
            if not text or len(text) < 20:
                logger.debug("Page %d of '%s' has no usable text — skipped.", page_num + 1, filename)
                continue

            pages.append({
                "page": page_num + 1,
                "text": text,
                "source": filename,
            })

        doc.close()
        logger.info(
            "extract_text_from_pdf: Extracted %d text-bearing pages from '%s'.",
            len(pages),
            filename,
        )

    except Exception as exc:
        logger.error("extract_text_from_pdf: Failed to process '%s' — %s", filename, exc)
        raise RuntimeError(f"PDF extraction failed for '{filename}': {exc}") from exc

    if not pages:
        raise RuntimeError(
            f"No extractable text found in '{filename}'. "
            "The PDF may be image-only (scanned). "
            "Please upload a text-layer PDF."
        )

    return pages
