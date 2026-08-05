"""
LexFusion Cross-Examine — Debate Graph
=======================================
LangGraph StateGraph that orchestrates a structured legal debate between
two AI advocates, followed by a synthesis judge node.

Graph Flow:
    START
      │
      ▼
  [advocate_a_node]   ← Round 1: Prosecution opens
      │
      ▼
  [advocate_b_node]   ← Round 1: Defence responds
      │
      ▼
  [check_rounds] ──► (rounds < MAX_ROUNDS) ──► [advocate_a_node]  (loop)
      │
      ▼ (rounds == MAX_ROUNDS)
  [synthesis_node]    ← Judge delivers final ruling
      │
      ▼
    END
"""

from __future__ import annotations

import os
from typing import Literal

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import END, START, StateGraph

from agents.prompts.advocate_a_prompt import get_advocate_a_messages
from agents.prompts.advocate_b_prompt import get_advocate_b_messages
from agents.prompts.synthesis_prompt import get_synthesis_messages
from agents.schemas import DebateState

load_dotenv()

# ── Configuration ────────────────────────────────────────────────────────────

MAX_DEBATE_ROUNDS = int(os.getenv("MAX_DEBATE_ROUNDS", "2"))
LLM_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))


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


def _get_llm() -> ChatGroq:
    """Instantiate the Groq LLM. Raises clearly if API key is missing."""
    api_key = _get_api_key()
    if not api_key:
        raise EnvironmentError(
            "GROQ_API_KEY is not set. Add it to your .env file or Streamlit secrets.\n"
            "Get a free key at: https://console.groq.com"
        )
    return ChatGroq(
        model=LLM_MODEL,
        temperature=LLM_TEMPERATURE,
        api_key=api_key,
    )


# ── Node Implementations ─────────────────────────────────────────────────────


def advocate_a_node(state: DebateState) -> dict:
    """
    Prosecution node — Advocate A argues the affirmative/plaintiff position.
    On round > 1, it rebuts Advocate B's previous argument.
    Returns only the updated keys (LangGraph merges into state automatically).
    """
    llm = _get_llm()

    # Get Advocate B's last argument (empty string on round 1)
    opponent_arg = state.get("advocate_b_argument", "None — opening argument.")
    round_num = state.get("current_round", 1)
    language = state.get("language", "English")

    messages = get_advocate_a_messages(
        query=state["query"],
        context=state["context"],
        opponent_argument=opponent_arg,
        round_number=round_num,
        language=language,
    )

    response = llm.invoke(messages)
    argument_text = response.content.strip()

    # Copy list before appending — avoids mutating state in-place
    history = list(state.get("argument_history", []))
    history.append(
        {
            "round": round_num,
            "advocate": "A",
            "role": "Prosecution",
            "argument": argument_text,
        }
    )

    # Return ONLY updated keys — LangGraph merges these into the shared state
    return {
        "advocate_a_argument": argument_text,
        "argument_history": history,
    }


def advocate_b_node(state: DebateState) -> dict:
    """
    Defence node — Advocate B argues the respondent/defence position.
    Always rebuts Advocate A's most recent argument.
    Returns only the updated keys (LangGraph merges into state automatically).
    """
    llm = _get_llm()

    round_num = state.get("current_round", 1)
    language = state.get("language", "English")

    messages = get_advocate_b_messages(
        query=state["query"],
        context=state["context"],
        opponent_argument=state.get("advocate_a_argument", ""),
        round_number=round_num,
        language=language,
    )

    response = llm.invoke(messages)
    argument_text = response.content.strip()

    # Copy list before appending — avoids mutating state in-place
    history = list(state.get("argument_history", []))
    history.append(
        {
            "round": round_num,
            "advocate": "B",
            "role": "Defence",
            "argument": argument_text,
        }
    )

    # Increment round counter after both advocates have spoken
    # Return ONLY updated keys — LangGraph merges these into the shared state
    return {
        "advocate_b_argument": argument_text,
        "argument_history": history,
        "current_round": round_num + 1,
    }


def synthesis_node(state: DebateState) -> dict:
    """
    Judge node — synthesizes all arguments into a balanced final ruling.
    Extracts a confidence score from the LLM response text.
    Returns only the updated keys (LangGraph merges into state automatically).
    """
    llm = _get_llm()
    language = state.get("language", "English")

    messages = get_synthesis_messages(
        query=state["query"],
        context=state["context"],
        advocate_a_argument=state.get("advocate_a_argument", ""),
        advocate_b_argument=state.get("advocate_b_argument", ""),
        total_rounds=state.get("current_round", 1) - 1,
        language=language,
    )

    response = llm.invoke(messages)
    synthesis_text = response.content.strip()

    # Best-effort confidence score extraction
    confidence = _extract_confidence(synthesis_text)

    # Return ONLY updated keys — LangGraph merges these into the shared state
    return {
        "synthesis": synthesis_text,
        "confidence_score": confidence,
        "status": "complete",
    }


def _extract_confidence(text: str) -> int:
    """
    Parses the confidence score (e.g. '87%') from the synthesis output.
    Returns 50 as a safe default if parsing fails.
    """
    import re

    patterns = [
        r"confidence score[:\s]*(\d{1,3})[%]",
        r"\[(\d{1,3})\]%",
        r"(\d{1,3})%\s*confidence",
        r"confidence[:\s]+(\d{1,3})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            score = int(match.group(1))
            if 0 <= score <= 100:
                return score
    return 50  # Default neutral confidence


# ── Conditional Edge ──────────────────────────────────────────────────────────


def should_continue_debate(state: DebateState) -> Literal["continue", "synthesize"]:
    """
    Routing function: continue debate if rounds remain, else move to synthesis.
    Re-reads MAX_DEBATE_ROUNDS from the environment at call time so that a
    per-request override written by run_debate() (via os.environ) is honoured —
    the module-level constant is captured at import time and would otherwise
    ignore any runtime change.
    """
    current_round = state.get("current_round", 1)
    max_rounds = int(os.getenv("MAX_DEBATE_ROUNDS", str(MAX_DEBATE_ROUNDS)))
    if current_round <= max_rounds:
        return "continue"
    return "synthesize"


# ── Graph Assembly ────────────────────────────────────────────────────────────


def build_debate_graph():
    """
    Constructs and compiles the LangGraph StateGraph for the Cross-Examine debate.

    Returns:
        A compiled LangGraph runnable ready for .invoke() calls.
    """
    graph = StateGraph(DebateState)

    # Register all nodes
    graph.add_node("advocate_a", advocate_a_node)
    graph.add_node("advocate_b", advocate_b_node)
    graph.add_node("judge_synthesis", synthesis_node)

    # Entry point: prosecution always opens
    graph.add_edge(START, "advocate_a")

    # After prosecution speaks → defence responds
    graph.add_edge("advocate_a", "advocate_b")

    # After defence responds → decide: another round or synthesize?
    graph.add_conditional_edges(
        "advocate_b",
        should_continue_debate,
        {
            "continue": "advocate_a",   # Another round of debate
            "synthesize": "judge_synthesis",  # Enough rounds — judge rules
        },
    )

    # After synthesis → done
    graph.add_edge("judge_synthesis", END)

    return graph.compile()


# ── Module-level compiled graph (singleton) ──────────────────────────────────

debate_graph = build_debate_graph()
