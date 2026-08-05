"""
LexFusion Cross-Examine — Main Agent Entry Point
=================================================
Public interface for the agents module. Exposes two primary functions:

  1. generate_answer()  — Single-shot RAG: retrieve + synthesize, no debate.
  2. run_debate()       — Full Cross-Examine debate via the LangGraph graph.

The backend (api/main.py) calls these functions directly.
"""

from __future__ import annotations

import os
import logging
from typing import Any

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from agents.debate_graph import debate_graph
from agents.prompts.synthesis_prompt import get_synthesis_messages
from agents.schemas import DebateResponse, DebateRound, GenerateResponse

load_dotenv()

logger = logging.getLogger(__name__)


def _get_api_key() -> str:
    """
    Read Groq API key — checks Streamlit secrets first (for Streamlit Cloud),
    then falls back to environment variable (for local .env usage).
    """
    try:
        import streamlit as st
        key = st.secrets.get("GROQ_API_KEY", "")
        if key:
            return key
    except Exception:
        pass
    return os.getenv("GROQ_API_KEY", "")


# ── Single-Shot RAG Answer ────────────────────────────────────────────────────

SINGLE_SHOT_SYSTEM = """
You are LexFusion, an expert AI legal research assistant.
Answer the user's legal question based ONLY on the provided context documents.
Be precise, cite relevant sections, and always end with a legal disclaimer.
If the context is insufficient, say so explicitly — never hallucinate.

Structure your answer:
1. **Direct Answer** — Concise response to the question.
2. **Legal Basis** — Cite clauses/sections from the context.
3. **Analysis** — Brief reasoning.
4. **Disclaimer** — Standard legal disclaimer.

LANGUAGE DIRECTIVE:
{language_directive}
"""


def generate_answer(
    query: str,
    context: str,
    source_documents: list[dict[str, Any]] | None = None,
    language: str = "English",
) -> GenerateResponse:
    """
    Single-shot RAG answer: no debate, just retrieve + synthesize.

    Args:
        query:            The user's legal question.
        context:          Pre-formatted string of retrieved document chunks.
        source_documents: Metadata list for the retrieved chunks.
        language:         Language for the AI response (default: English).

    Returns:
        GenerateResponse with answer, sources, and confidence score.

    Raises:
        EnvironmentError: If GROQ_API_KEY is not configured.
        RuntimeError: If the LLM call fails.
    """
    api_key = _get_api_key()
    if not api_key:
        raise EnvironmentError(
            "GROQ_API_KEY is not set. Add it to your .env file or Streamlit secrets.\n"
            "Free key: https://console.groq.com"
        )

    llm = ChatGroq(
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        temperature=float(os.getenv("LLM_TEMPERATURE", "0.2")),
        api_key=api_key,
    )

    if language.lower() == "english":
        language_directive = "Respond in English (default)."
    else:
        language_directive = (
            f"CRITICAL: You MUST respond ENTIRELY in {language}. "
            f"Every word, heading, analysis, and disclaimer must be in {language} only. "
            f"Do NOT use English or any other language."
        )

    system_prompt = SINGLE_SHOT_SYSTEM.format(language_directive=language_directive)

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": (
                f"LEGAL QUESTION:\n{query}\n\n"
                f"RETRIEVED CONTEXT:\n{context}\n\n"
                "Please provide a grounded legal answer."
            ),
        },
    ]

    try:
        response = llm.invoke(messages)
        answer_text = response.content.strip()
        logger.info("generate_answer: LLM call successful for query: %s...", query[:60])
    except Exception as exc:
        logger.error("generate_answer: LLM call failed — %s", exc)
        raise RuntimeError(f"LLM inference failed: {exc}") from exc

    return GenerateResponse(
        query=query,
        answer=answer_text,
        source_documents=source_documents or [],
        confidence_score=_estimate_single_confidence(answer_text, context),
    )


def _estimate_single_confidence(answer: str, context: str) -> int:
    """
    Heuristic confidence estimation for single-shot answers.
    Higher when answer is longer (more detailed) and context is rich.
    """
    answer_len = len(answer.split())
    context_len = len(context.split())

    if context_len < 50:
        return 30  # Very little context → low confidence
    if answer_len < 30:
        return 40  # Very short answer → uncertain
    if "insufficient" in answer.lower() or "cannot determine" in answer.lower():
        return 25  # LLM admitted uncertainty
    if context_len > 500 and answer_len > 100:
        return 82  # Rich context + detailed answer
    return 65  # Default moderate confidence


# ── Full Cross-Examine Debate ─────────────────────────────────────────────────


def run_debate(
    query: str,
    context: str,
    source_documents: list[dict[str, Any]] | None = None,
    max_rounds: int | None = None,
    language: str = "English",
) -> DebateResponse:
    """
    Run the full LangGraph Cross-Examine debate graph.

    Two AI advocates (Prosecution + Defence) argue multiple rounds,
    followed by a Judge synthesis node delivering a final ruling.

    Args:
        query:            The user's legal question.
        context:          Pre-formatted string of retrieved document chunks.
        source_documents: Metadata list for the retrieved chunks.
        max_rounds:       Override MAX_DEBATE_ROUNDS env var for this call.
        language:         Language for all agent responses (default: English).

    Returns:
        DebateResponse with full argument history, synthesis, confidence, and sources.

    Raises:
        EnvironmentError: If GROQ_API_KEY is not configured.
        RuntimeError: If the graph execution fails.
    """
    if not _get_api_key():
        raise EnvironmentError(
            "GROQ_API_KEY is not set. Add it to your .env file or Streamlit secrets.\n"
            "Free key: https://console.groq.com"
        )

    # Override max rounds if specified per-request
    if max_rounds is not None:
        os.environ["MAX_DEBATE_ROUNDS"] = str(max_rounds)

    initial_state: dict[str, Any] = {
        "query": query,
        "context": context,
        "source_documents": source_documents or [],
        "advocate_a_argument": "",
        "advocate_b_argument": "",
        "argument_history": [],
        "current_round": 1,
        "synthesis": "",
        "confidence_score": 50,
        "status": "running",
        "error_message": "",
        "language": language,
    }

    try:
        logger.info("run_debate: Starting debate graph for query: %s...", query[:60])
        final_state = debate_graph.invoke(initial_state)
        logger.info(
            "run_debate: Graph completed. Status: %s | Confidence: %s%%",
            final_state.get("status"),
            final_state.get("confidence_score"),
        )
    except Exception as exc:
        logger.error("run_debate: Graph execution failed — %s", exc)
        raise RuntimeError(f"Debate graph execution failed: {exc}") from exc

    # Coerce argument_history dicts → DebateRound models
    history = [
        DebateRound(**entry) for entry in final_state.get("argument_history", [])
    ]

    return DebateResponse(
        query=query,
        argument_history=history,
        synthesis=final_state.get("synthesis", "Synthesis unavailable."),
        confidence_score=final_state.get("confidence_score", 50),
        source_documents=final_state.get("source_documents", []),
        status=final_state.get("status", "complete"),
    )
