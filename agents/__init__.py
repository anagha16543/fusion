# LexFusion Cross-Examine — Agents Module
# =========================================
# Public re-exports for the agents package.
# Import these from the backend via: from agents import generate_answer, run_debate

from agents.generate import generate_answer, run_debate
from agents.schemas import (
    DebateResponse,
    DebateRound,
    DebateState,
    GenerateResponse,
    QueryRequest,
)
from agents.debate_graph import debate_graph, build_debate_graph

__all__ = [
    "generate_answer",
    "run_debate",
    "debate_graph",
    "build_debate_graph",
    "DebateState",
    "DebateResponse",
    "DebateRound",
    "GenerateResponse",
    "QueryRequest",
]
