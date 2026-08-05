"""
LexFusion — Backend Pydantic Models
======================================
Shared request/response models for the optional FastAPI server layer.
"""

from __future__ import annotations

from typing import Any, List, Optional
from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    """Response returned after a successful PDF ingestion."""
    status: str = Field(..., description="'success' or 'error'")
    filename: str = Field(..., description="Name of the ingested file.")
    pages_extracted: int = Field(default=0, description="Number of text-bearing pages parsed.")
    chunks_added: int = Field(default=0, description="Number of vector chunks indexed.")
    message: str = Field(default="", description="Human-readable status message.")


class StatsResponse(BaseModel):
    """Vector store statistics."""
    chunk_count: int = Field(default=0, description="Total chunks indexed.")
    collection: str = Field(default="lexfusion_legal_docs")
    status: str = Field(default="empty")


class QueryRequest(BaseModel):
    """Request body for the /query endpoint."""
    query: str = Field(..., min_length=5, max_length=2000)
    debate_mode: bool = Field(default=True)
    top_k: int = Field(default=5, ge=1, le=20)
    max_rounds: Optional[int] = Field(default=None, ge=1, le=5)
    language: str = Field(default="English", description="Response language for AI agents.")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "ok"
    version: str = "1.0.0"
    service: str = "LexFusion API"
