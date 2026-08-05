"""
LexFusion Single-Shot RAG Assistant Page
=========================================
Simple, clean conversational chat interface for asking direct
legal questions about the uploaded document corpus.
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
from components.answer_card import render_source_cards


def render_chat_page(client: LexFusionAPIClient):
    """Renders the single-shot RAG Chat assistant."""
    # Read selected language from sidebar session state
    language = st.session_state.get("selected_language", "English")
    lang_flag = "🌍" if language != "English" else "💬"

    st.markdown(
        f"""
        <div style="margin-bottom: 25px;">
            <h1 class="court-title" style="font-size: 2.2rem; margin-bottom: 5px;">
                {lang_flag} Legal <span class="gold-text">Research Assistant</span>
            </h1>
            <p style="color: #9ca3af; font-size: 1rem;">
                Ask direct legal questions to analyze terms, obligations, and clauses in your document corpus.
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
                🌐 Responding in: {language}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Initialize message history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Clear chat when language changes
    if st.session_state.get("_last_chat_language") != language:
        st.session_state.chat_history = []
        st.session_state["_last_chat_language"] = language

    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "sources" in message and message["sources"]:
                render_source_cards(message["sources"])

    # User input
    if prompt := st.chat_input(f"Enter your legal question... (response will be in {language})"):
        # Display user message
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Call RAG API (non-debate mode) with selected language
        with st.chat_message("assistant"):
            with st.spinner(f"Analyzing document corpus and generating {language} response..."):
                response = client.query(
                    query=prompt,
                    debate_mode=False,
                    language=language,
                )

            if "answer" in response:
                answer = response["answer"]
                sources = response.get("source_documents", [])

                st.markdown(answer)
                render_source_cards(sources)

                # Store assistant response
                st.session_state.chat_history.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "sources": sources,
                    }
                )
            else:
                err_msg = response.get("error_message", "Inference failed.")
                st.error(f"Error analyzing query: {err_msg}")
