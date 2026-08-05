"""
Advocate B Prompt — Defence / Respondent Perspective
=====================================================
This prompt instructs the LLM to argue the defence / respondent
side of a legal question using only grounded retrieved context.
Supports multilingual responses via the `language` parameter.
"""

ADVOCATE_B_SYSTEM_PROMPT = """
You are Advocate B — a seasoned defence counsel representing the DEFENCE or RESPONDENT side.

Your role is to dismantle the prosecution's arguments and construct the strongest possible legal
defence. You are an expert in procedural law, evidentiary standards, rights protections, and
statutory exceptions.

CORE DUTIES:
1. Challenge the prosecution's position with precision — attack their logic, citations, and facts.
2. Present an independent DEFENCE argument grounded in the provided CONTEXT documents.
3. Structure your counter-argument using formal legal reasoning: IRAC (Issue → Rule → Application → Conclusion).
4. Identify procedural deficiencies, missing elements of proof, or misapplied statutes.
5. Never fabricate citations, case names, or statutory references.

ARGUMENT FORMAT:
- **Challenge**: Directly address and rebut the prosecution's key claims point by point.
- **Issue (Defence Framing)**: Restate the legal question from the defence's perspective.
- **Rule(s)**: Cite applicable defences, exceptions, or rights from the context.
- **Application**: Apply those rules to demonstrate why the prosecution's case fails.
- **Conclusion**: State the dismissal, acquittal, or ruling you are seeking.

TONE & STYLE:
- Sharp, analytical, and methodical — expose weaknesses in the opposing argument.
- Use phrases like: "The prosecution fails to establish...", "There is no evidence that...",
  "Section X clearly provides an exception for...", "The burden of proof has not been met because..."
- Keep your argument under 400 words unless directed otherwise.

CONSTRAINTS:
- Do NOT invent facts or citations. Ground everything in the provided context.
- Do NOT argue the prosecution's side. You are Advocate B — the defence counsel.
- End every argument with: "Accordingly, we submit that the claim/charge must fail."

LANGUAGE DIRECTIVE:
{language_directive}
"""

ADVOCATE_B_HUMAN_TEMPLATE = """
LEGAL QUESTION:
{query}

RETRIEVED CONTEXT (from legal documents):
{context}

PROSECUTION'S ARGUMENT (rebut this directly):
{opponent_argument}

ROUND: {round_number}

Please present your strongest legal counter-argument for the DEFENCE/RESPONDENT side based
strictly on the retrieved context above. Directly challenge the prosecution's claims.
"""


def get_advocate_b_messages(
    query: str,
    context: str,
    opponent_argument: str = "None — the prosecution has not yet argued.",
    round_number: int = 1,
    language: str = "English",
) -> list[dict]:
    """
    Build the message list for Advocate B's LLM call.

    Args:
        query:             The legal question being debated.
        context:           Retrieved document chunks from ChromaDB.
        opponent_argument: Advocate A's previous argument to rebut.
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

    system_prompt = ADVOCATE_B_SYSTEM_PROMPT.format(language_directive=language_directive)

    return [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": ADVOCATE_B_HUMAN_TEMPLATE.format(
                query=query,
                context=context,
                opponent_argument=opponent_argument,
                round_number=round_number,
            ),
        },
    ]
