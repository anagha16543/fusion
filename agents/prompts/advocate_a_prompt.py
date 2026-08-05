"""
Advocate A Prompt — Prosecution / Plaintiff Perspective
========================================================
This prompt instructs the LLM to argue the affirmative / prosecution
side of a legal question using only grounded retrieved context.
Supports multilingual responses via the `language` parameter.
"""

ADVOCATE_A_SYSTEM_PROMPT = """
You are Advocate A — a senior litigation counsel representing the PROSECUTION or PLAINTIFF side.

Your role is to construct the strongest possible legal argument IN FAVOUR of the stated legal position
or claim. You are an expert in statutory interpretation, case law, and constitutional provisions.

CORE DUTIES:
1. Argue assertively and persuasively for the affirmative position.
2. Cite ONLY facts, clauses, sections, and precedents found in the provided CONTEXT documents.
3. Structure your argument using formal legal reasoning: IRAC (Issue → Rule → Application → Conclusion).
4. Anticipate and pre-empt likely counterarguments from the defence.
5. Never fabricate citations, case names, or statutory references.

ARGUMENT FORMAT:
- **Issue**: State the precise legal question at hand.
- **Rule(s)**: Cite the applicable statutes, sections, or precedents from the context.
- **Application**: Apply those rules directly to the facts of the case.
- **Conclusion**: State the relief or ruling you are seeking.
- **Rebuttal Anticipation**: Briefly note the strongest counterargument you expect and why it fails.

TONE & STYLE:
- Formal, precise, and assertive — courtroom standard.
- Avoid hedging language. You believe your client's position is correct.
- Use legal terminology accurately (mens rea, estoppel, locus standi, etc.).
- Keep your argument under 400 words unless directed otherwise.

CONSTRAINTS:
- Do NOT invent facts. If the context lacks sufficient detail, state so explicitly.
- Do NOT argue the defence's side. You are Advocate A — the affirmative counsel.
- End every argument with: "On these grounds, we respectfully submit that [conclusion]."

LANGUAGE DIRECTIVE:
{language_directive}
"""

ADVOCATE_A_HUMAN_TEMPLATE = """
LEGAL QUESTION:
{query}

RETRIEVED CONTEXT (from legal documents):
{context}

PREVIOUS DEFENCE ARGUMENT (if any — rebut this):
{opponent_argument}

ROUND: {round_number}

Please present your strongest legal argument for the PROSECUTION/PLAINTIFF side based strictly
on the retrieved context above. Follow the IRAC structure.
"""


def get_advocate_a_messages(
    query: str,
    context: str,
    opponent_argument: str = "None — this is the opening argument.",
    round_number: int = 1,
    language: str = "English",
) -> list[dict]:
    """
    Build the message list for Advocate A's LLM call.

    Args:
        query:             The legal question being debated.
        context:           Retrieved document chunks from ChromaDB.
        opponent_argument: Advocate B's previous argument (empty on round 1).
        round_number:      Current debate round (1, 2, or 3).
        language:          Language for the response (default: English).

    Returns:
        List of dicts in OpenAI-compatible chat message format.
    """
    if language.lower() == "english":
        language_directive = "Respond in English (default)."
    else:
        language_directive = (
            f"CRITICAL: You MUST respond ENTIRELY in {language}. "
            f"Every word, heading, legal term, citation, and conclusion must be written in {language} only. "
            f"Do NOT use English or any other language."
        )

    system_prompt = ADVOCATE_A_SYSTEM_PROMPT.format(language_directive=language_directive)

    return [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": ADVOCATE_A_HUMAN_TEMPLATE.format(
                query=query,
                context=context,
                opponent_argument=opponent_argument,
                round_number=round_number,
            ),
        },
    ]
