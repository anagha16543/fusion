"""
LexFusion — Embedding Model
============================
Singleton wrapper for sentence-transformers/all-MiniLM-L6-v2.
Runs fully in-process — no external API key required.
Cached at module level to avoid reloading the model on each call.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

# Disable TensorFlow/Keras backends in transformers BEFORE any import of
# sentence-transformers or transformers.  Without this, transformers tries to
# import tf-keras, which breaks on Keras 3 with:
#   "Your currently installed version of Keras is Keras 3, but this is not yet
#    supported in Transformers."
os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
os.environ.setdefault("USE_TF", "0")

logger = logging.getLogger(__name__)

# Module-level singleton — loaded once per Python process
_embeddings_instance = None


def get_embeddings():
    """
    Return the singleton HuggingFaceEmbeddings instance.
    Downloads the model on first call (~90 MB), then reuses it.

    Returns:
        HuggingFaceEmbeddings instance using all-MiniLM-L6-v2.

    Raises:
        ImportError: If langchain-huggingface or sentence-transformers is missing.
    """
    global _embeddings_instance

    if _embeddings_instance is not None:
        return _embeddings_instance

    try:
        from langchain_huggingface import HuggingFaceEmbeddings
    except ImportError as exc:
        raise ImportError(
            "langchain-huggingface and sentence-transformers are required. "
            "Install with: pip install langchain-huggingface sentence-transformers"
        ) from exc

    logger.info("get_embeddings: Loading sentence-transformers/all-MiniLM-L6-v2...")

    _embeddings_instance = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    logger.info("get_embeddings: Model loaded successfully.")
    return _embeddings_instance
