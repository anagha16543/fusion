"""
LexFusion Cross-Examine ΓÇö Pydantic Schemas for Agent State
===========================================================
Defines the TypedDict state that flows through the LangGraph debate graph,
plus Pydantic response models for API serialization.
"""

from __future__ import annotations

from typing import Any, Optional
from typing_extensions import TypedDict
from pydantic import BaseModel, Field, field_validator


# ΓöÇΓöÇ LangGraph Agent State ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ


class DebateState(TypedDict, total=False):
    """
    Shared mutable state that flows through every node of the debate graph.

    Fields:
        query:                The original legal question from the user.
        context:              Retrieved document chunks (pre-formatted as a string).
        source_documents:     List of source metadata dicts [{source, page, chunk}, ...].
        advocate_a_argument:  Most recent argument from Advocate A (Prosecution).
        advocate_b_argument:  Most recent argument from Advocate B (Defence).
        argument_history:     Full ordered list of all arguments across all rounds.
        current_round:        Current debate round number (starts at 1).
        synthesis:            Final judge ruling / synthesis text.
        confidence_score:     Integer 0ΓÇô100 extracted from synthesis.
        status:               "running" | "complete" | "error"
        error_message:        Human-readable error string if status == "error".
        language:             Language for all agent responses (default: "English").
    """

    query: str
    context: str
    source_documents: list[dict[str, Any]]
    advocate_a_argument: str
    advocate_b_argument: str
    argument_history: list[dict[str, Any]]
    current_round: int
    synthesis: str
    confidence_score: int
    status: str
    error_message: str
    language: str


# ΓöÇΓöÇ Pydantic API Response Models ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ


class DebateRound(BaseModel):
    """A single advocate's argument in one round of the debate."""

    round: int = Field(..., ge=1, description="Round number (1-indexed).")
    advocate: str = Field(..., description="'A' (Prosecution) or 'B' (Defence).")
    role: str = Field(..., description="Human-readable role label.")
    argument: str = Field(..., description="Full argument text from the LLM.")


class DebateResponse(BaseModel):
    """
    Full structured response returned by the /debate API endpoint.
    Mirrors the final DebateState after the graph completes.
    """

    query: str = Field(..., description="The original legal question.")
    argument_history: list[DebateRound] = Field(
        default_factory=list,
        description="Ordered list of all advocate arguments across all debate rounds.",
    )
    synthesis: str = Field(
        ..., description="Final judge ruling synthesizing both positions."
    )
    confidence_score: int = Field(
        default=50,
        ge=0,
        le=100,
        description="AI confidence (0ΓÇô100%) in the legal finding.",
    )
    source_documents: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Source document metadata for retrieved chunks.",
    )
    status: str = Field(default="complete", description="'complete' or 'error'.")

    @field_validator("confidence_score")
    @classmethod
    def clamp_confidence(cls, v: int) -> int:
        return max(0, min(100, v))


class GenerateResponse(BaseModel):
    """
    Simpler response for single-shot RAG answer (non-debate mode).
    Used by the /generate endpoint.
    """

    query: str = Field(..., description="The original legal question.")
    answer: str = Field(..., description="AI-generated answer grounded in context.")
    source_documents: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Source document metadata.",
    )
    confidence_score: int = Field(default=75, ge=0, le=100)
    disclaimer: str = Field(
        default=(
            "This AI-generated analysis is for informational purposes only "
            "and does not constitute legal advice. Consult a qualified legal "
            "professional for binding guidance."
        )
    )


class QueryRequest(BaseModel):
    """Request body for both /generate and /debate endpoints."""

    query: str = Field(
        ...,
        min_length=5,
        max_length=2000,
        description="Legal question to ask the system.",
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of document chunks to retrieve from vector store.",
    )
    debate_mode: bool = Field(
        default=True,
        description="If True, run full Cross-Examine debate. If False, single-shot RAG.",
    )
    max_rounds: Optional[int] = Field(
        default=None,
        ge=1,
        le=5,
        description="Override MAX_DEBATE_ROUNDS for this request.",
    )
    language: str = Field(
        default="English",
        description="Language for all agent responses (Advocate A, B, and Judge).",
    )
