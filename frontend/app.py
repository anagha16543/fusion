"""
LexFusion — Primary Streamlit Application Entry Point
======================================================
Combines subpages, sidebar parameters, custom styling,
language selector, and file uploading with premium UI assets.
"""

from __future__ import annotations

import os
import sys
import streamlit as st

# Setup paths to ensure we can load utilities cleanly
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.api_client import LexFusionAPIClient
from pages.chat import render_chat_page
from pages.debate import render_debate_page

# ── 50 Supported Languages ────────────────────────────────────────────────────

SUPPORTED_LANGUAGES = [
    # European
    "English", "Spanish", "French", "German", "Italian", "Dutch", "Portuguese",
    "Russian", "Polish", "Swedish", "Norwegian", "Danish", "Finnish", "Greek",
    "Romanian", "Czech", "Hungarian", "Slovak", "Croatian", "Ukrainian",
    # Middle East / Central Asia
    "Arabic", "Hebrew", "Turkish", "Kazakh",
    # South Asia
    "Hindi", "Bengali", "Urdu", "Punjabi", "Tamil", "Telugu", "Kannada",
    "Malayalam", "Gujarati", "Marathi", "Odia", "Nepali", "Sinhala",
    # East / Southeast Asia
    "Chinese (Simplified)", "Chinese (Traditional)", "Japanese", "Korean",
    "Thai", "Vietnamese", "Indonesian", "Malay", "Burmese", "Khmer",
    "Lao", "Mongolian",
    # Africa
    "Swahili", "Amharic",
]

# Set page configurations
st.set_page_config(
    page_title="LexFusion — Law RAG Workflow Automation",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)


def load_custom_css():
    """Loads and injects the premium static CSS stylesheet."""
    css_path = os.path.join(os.path.dirname(__file__), "static", "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def main():
    # Load custom courtroom dark/gold theme stylesheet
    load_custom_css()

    # Initialize the API / Local Direct Mode client (once per session)
    if "api_client" not in st.session_state:
        with st.spinner("🏛️ Initializing LexFusion — loading embedding model..."):
            st.session_state.api_client = LexFusionAPIClient()
    client: LexFusionAPIClient = st.session_state.api_client

    # ── Sidebar Branding ──────────────────────────────────────────────────────
    st.sidebar.markdown(
        """
        <div style="text-align: center; margin-bottom: 20px;">
            <h2 class="court-title" style="font-size: 1.8rem; margin: 0; color: #c9a84c;">
                🏛️ LEXFUSION
            </h2>
            <span style="font-size: 0.75rem; letter-spacing: 2px; color: #9ca3af; text-transform: uppercase;">
                Legal RAG Chamber
            </span>
        </div>
        <hr style="border-color: rgba(255,255,255,0.08); margin-top: 5px; margin-bottom: 20px;" />
        """,
        unsafe_allow_html=True,
    )

    # ── Language Selector ─────────────────────────────────────────────────────
    st.sidebar.markdown("### 🌐 Response Language")

    selected_language = st.sidebar.selectbox(
        "Select Language",
        options=SUPPORTED_LANGUAGES,
        index=0,  # Default: English
        key="selected_language",
        help="All AI agents (Advocate A, Advocate B, and the Judge) will respond in this language.",
        label_visibility="collapsed",
    )

    # Language badge display
    lang_emoji = "🌍" if selected_language != "English" else "🇬🇧"
    st.sidebar.markdown(
        f"""
        <div style="text-align:center; margin-bottom: 18px; margin-top: -8px;">
            <span style="
                background: rgba(201,168,76,0.12);
                border: 1px solid rgba(201,168,76,0.35);
                border-radius: 999px;
                padding: 4px 14px;
                font-size: 0.8rem;
                color: #c9a84c;
                font-weight: 600;
                letter-spacing: 0.5px;
            ">
                {lang_emoji} {selected_language}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Document Ingestion ────────────────────────────────────────────────────
    st.sidebar.markdown("### 📥 Ingest Documents")
    uploaded_files = st.sidebar.file_uploader(
        "Upload Legal PDFs",
        type=["pdf"],
        accept_multiple_files=True,
        help="Upload contracts, court rulings, or case briefs for analysis.",
    )

    if uploaded_files:
        for file in uploaded_files:
            if f"uploaded_{file.name}" not in st.session_state:
                with st.sidebar.spinner(f"Ingesting {file.name}..."):
                    res = client.upload_document(file.name, file.read())
                    if res.get("status") == "success":
                        chunks = res.get("chunks_added", res.get("chunk_count", 0))
                        pages = res.get("pages_extracted", "?")
                        st.sidebar.success(
                            f"✅ **{file.name}**\n{pages} pages → {chunks} chunks indexed"
                        )
                        st.session_state[f"uploaded_{file.name}"] = True
                    else:
                        st.sidebar.error(f"❌ Failed: {res.get('message', file.name)}")

    # ── Vector Store Stats ────────────────────────────────────────────────────
    stats = client.get_stats()
    chunk_count = stats.get("chunk_count", 0)
    store_status = "🟢 READY" if chunk_count > 0 else "🟡 EMPTY"

    st.sidebar.markdown(
        f"""
        <div class="glass-card" style="margin-top: 16px; padding: 12px; background: rgba(255,255,255,0.02);">
            <div style="font-size: 0.78rem; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;">
                Vector Database
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                <span style="font-size:0.85rem;">📊 Status:</span>
                <span class="gold-text" style="font-weight: 600; font-size:0.85rem;">{store_status}</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
                <span style="font-size:0.85rem;">🔢 Chunks Indexed:</span>
                <span style="font-weight: 600; font-size:0.85rem;">{chunk_count:,}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Navigation ────────────────────────────────────────────────────────────
    st.sidebar.markdown("### 🧭 Navigation")
    app_mode = st.sidebar.radio(
        "Select Chamber Interface",
        ["💬 Chat Assistant", "⚖️ Cross-Examine Debate"],
        label_visibility="collapsed",
    )

    # ── Network Status Badge ──────────────────────────────────────────────────
    mode_label = "LOCAL / CLOUD MODE" if client.local_mode else "API SERVER CONNECTED"
    mode_color = "#f59e0b" if client.local_mode else "#10b981"
    mode_dot = "🟡" if client.local_mode else "🟢"

    st.sidebar.markdown(
        f"""
        <div style="position: fixed; bottom: 20px; left: 20px; width: 260px;">
            <div style="text-align: center;">
                <span style="
                    background: rgba(255,255,255,0.04);
                    border: 1px solid rgba(255,255,255,0.1);
                    border-radius: 999px;
                    padding: 5px 14px;
                    font-size: 0.7rem;
                    color: {mode_color};
                    font-weight: 600;
                    letter-spacing: 0.5px;
                ">
                    {mode_dot} {mode_label}
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Render Page ───────────────────────────────────────────────────────────
    if app_mode == "💬 Chat Assistant":
        render_chat_page(client)
    else:
        render_debate_page(client)


if __name__ == "__main__":
    main()
