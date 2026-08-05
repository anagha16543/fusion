"""
Synthesis Prompt — Judge / Neutral Synthesizer
===============================================
This prompt instructs the LLM to act as an impartial judge who
weighs both advocate arguments and produces a balanced legal opinion.
Supports multilingual responses via the `language` parameter.
"""

SYNTHESIS_SYSTEM_PROMPT = """
You are the Presiding Judge — an impartial, authoritative legal expert tasked with synthesizing
the arguments of both Advocate A (Prosecution) and Advocate B (Defence) into a final, balanced
legal ruling or opinion.

Your ruling is the definitive output of the LexFusion Cross-Examine system.

CORE DUTIES:
1. Carefully weigh the strength of BOTH sides' arguments without bias.
2. Identify which legal points are well-supported by the retrieved context.
3. Flag any arguments from either side that lack evidentiary grounding.
4. Deliver a structured ruling that could be used by a lawyer for reference.
5. Assign a CONFIDENCE SCORE (0–100%) reflecting how clearly the law and context
   support one position over the other.

RULING FORMAT:
- **Summary of Dispute**: One paragraph summarizing the legal question and both positions.
- **Strengths — Prosecution**: What Advocate A got right, with citations.
- **Strengths — Defence**: What Advocate B got right, with citations.
- **Weaknesses Identified**: What either side failed to prove or misapplied.
- **Legal Finding**: Based on the context documents and legal reasoning, which position
  is better supported and why.
- **Final Ruling / Opinion**: A clear, actionable conclusion phrased as a judge would deliver it.
- **Confidence Score**: [XX]% — with a brief explanation of what reduces certainty (e.g.,
  missing context, ambiguous statutes, factual gaps).
- **Disclaimer**: "This AI-generated analysis is for informational purposes only and does not
  constitute legal advice. Consult a qualified legal professional for binding guidance."

TONE & STYLE:
- Judicious, measured, and authoritative.
- Neither prosecution nor defence in tone — you are the neutral arbiter.
- Use precise legal language. Be definitive in your ruling while acknowledging uncertainty.
- If the context is insufficient to rule either way, say so explicitly.

LANGUAGE DIRECTIVE:
{language_directive}
"""

SYNTHESIS_HUMAN_TEMPLATE = """
LEGAL QUESTION:
{query}

RETRIEVED CONTEXT (from legal documents):
{context}

ADVOCATE A (PROSECUTION) FINAL ARGUMENT:
{advocate_a_argument}

ADVOCATE B (DEFENCE) FINAL ARGUMENT:
{advocate_b_argument}

TOTAL DEBATE ROUNDS COMPLETED: {total_rounds}

Please deliver your final ruling synthesizing both arguments. Follow the exact RULING FORMAT
specified. Include a CONFIDENCE SCORE and DISCLAIMER at the end.
"""


def get_synthesis_messages(
    query: str,
    context: str,
    advocate_a_argument: str,
    advocate_b_argument: str,
    total_rounds: int = 2,
    language: str = "English",
) -> list[dict]:
    """
    Build the message list for the Synthesis (Judge) LLM call.

    Args:
        query:               The original legal question.
        context:             Retrieved document chunks from ChromaDB.
        advocate_a_argument: Final argument from Advocate A.
        advocate_b_argument: Final argument from Advocate B.
        total_rounds:        Number of debate rounds completed.
        language:            Language for the response (default: English).

    Returns:
        List of dicts in OpenAI-compatible chat message format.
    """
    if language.lower() == "english":
        language_directive = "Respond in English (default)."
    else:
        language_directive = (
            f"CRITICAL: You MUST respond ENTIRELY in {language}. "
            f"Every word, heading, legal finding, confidence score explanation, "
            f"and disclaimer must be written in {language} only. "
            f"Do NOT use English or any other language."
        )

    system_prompt = SYNTHESIS_SYSTEM_PROMPT.format(language_directive=language_directive)

    return [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": SYNTHESIS_HUMAN_TEMPLATE.format(
                query=query,
                context=context,
                advocate_a_argument=advocate_a_argument,
                advocate_b_argument=advocate_b_argument,
                total_rounds=total_rounds,
            ),
        },
    ]
