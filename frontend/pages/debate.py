"""
LexFusion Cross-Examine Debate Page
====================================
Immersive visual interface showing the multi-round courtroom debate
between Advocate A and Advocate B, concluding with a Judge synthesis.
Supports multilingual responses via the sidebar language selector.
"""

from __future__ import annotations

import os
import sys

# Ensure the frontend directory is on sys.path so that relative imports
# (utils, components) resolve correctly regardless of invocation CWD.
_here = os.path.dirname(os.path.abspath(__file__))           # .../frontend/pages
_frontend = os.path.abspath(os.path.join(_here, ".."))       # .../frontend
_project_root = os.path.abspath(os.path.join(_frontend, ".."))  # project root

for _p in (_project_root, _frontend):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import streamlit as st
from utils.api_client import LexFusionAPIClient
from components.advocate_column import render_debate_rounds
from components.answer_card import render_synthesis_card, render_source_cards


def render_debate_page(client: LexFusionAPIClient):
    """Renders the adversarial debate page."""
    # Read selected language from sidebar session state
    language = st.session_state.get("selected_language", "English")
    lang_flag = "🌍" if language != "English" else "⚖️"

    st.markdown(
        f"""
        <div style="margin-bottom: 25px;">
            <h1 class="court-title" style="font-size: 2.2rem; margin-bottom: 5px;">
                🏛️ Cross-Examine <span class="gold-text">Debate Chamber</span>
            </h1>
            <p style="color: #9ca3af; font-size: 1rem;">
                Run an adversarial AI-driven debate between Prosecution and Defence to uncover hidden loopholes and legal weaknesses.
            </p>
            <span style="
                background: rgba(201,168,76,0.1);
                border: 1px solid rgba(201,168,76,0.25);
                border-radius: 999px;
                padding: 3px 12px;
                font-size: 0.78rem;
                color: #c9a84c;
                font-weight: 600;
            ">
                🌐 All advocates debating in: {language}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Sidebar parameters for debate configuration
    st.sidebar.markdown("### 🎛️ Chamber Settings")
    debate_rounds = st.sidebar.slider("Debate Rounds", min_value=1, max_value=3, value=2)
    top_k = st.sidebar.slider("Evidence Retrieve Count (Top K)", min_value=3, max_value=10, value=5)

    # Input zone
    st.markdown("### ⚖️ File an Argument")
    user_query = st.text_area(
        "Define the legal issue/dispute to cross-examine:",
        placeholder="e.g., Is the vendor liable for damages if a data breach occurs due to a third-party API outage?",
        height=90,
    )

    if st.button("⚖️ Convene Courtroom", use_container_width=True):
        if not user_query.strip():
            st.warning("Please provide a legal query first.")
            return

        # Running indicator
        with st.status(
            f"Court is in session. Running Agentic Graph in {language}...",
            expanded=True
        ) as status:
            status.update(label=f"Advocates preparing arguments in {language}...", state="running")

            # Execute debate with selected language
            response = client.query(
                query=user_query,
                debate_mode=True,
                top_k=top_k,
                max_rounds=debate_rounds,
                language=language,
            )

            if response.get("status") == "complete" or "synthesis" in response:
                status.update(label="Rulings delivered by Presiding Judge.", state="complete")
                # Render results in session state to persist
                st.session_state.active_debate = response
                st.session_state.active_debate_language = language
            else:
                status.update(label="Court session errored.", state="error")
                err_msg = response.get("error_message", "Execution failed.")
                st.error(f"Court session aborted: {err_msg}")

    # Display active debate results
    if "active_debate" in st.session_state:
        res = st.session_state.active_debate
        debate_lang = st.session_state.get("active_debate_language", "English")

        # Language mismatch notice
        if debate_lang != language:
            st.info(
                f"ℹ️ This debate was conducted in **{debate_lang}**. "
                f"Press '⚖️ Convene Courtroom' again to run a new debate in **{language}**."
            )

        # Render the rounds of debate (Advocate A vs. Advocate B)
        render_debate_rounds(res.get("argument_history", []))

        st.markdown(
            "<hr style='border-color: rgba(255, 255, 255, 0.1); margin-top: 30px; margin-bottom: 30px;' />",
            unsafe_allow_html=True,
        )

        # Render the Judge ruling and confidence gauge
        render_synthesis_card(
            synthesis=res.get("synthesis", "Synthesis finding missing."),
            confidence_score=res.get("confidence_score", 50),
        )

        st.markdown("<br />", unsafe_allow_html=True)

        # Render sources
        render_source_cards(res.get("source_documents", []))
