"""
LexFusion — Primary Streamlit Application Entry Point
======================================================
Top-navigation bar layout with dark/light theme toggle.
Debate page uses animated step-by-step argument reveal.
"""

from __future__ import annotations

import os
import sys
import streamlit as st

# ── Path Setup ────────────────────────────────────────────────────────────────
_here = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.abspath(os.path.join(_here, ".."))
for _p in (_project_root, _here):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from utils.api_client import LexFusionAPIClient
from pages.chat import render_chat_page
from pages.debate import render_debate_page

# ── 50 Supported Languages ────────────────────────────────────────────────────
SUPPORTED_LANGUAGES = [
    "English", "Spanish", "French", "German", "Italian", "Dutch", "Portuguese",
    "Russian", "Polish", "Swedish", "Norwegian", "Danish", "Finnish", "Greek",
    "Romanian", "Czech", "Hungarian", "Slovak", "Croatian", "Ukrainian",
    "Arabic", "Hebrew", "Turkish", "Kazakh",
    "Hindi", "Bengali", "Urdu", "Punjabi", "Tamil", "Telugu", "Kannada",
    "Malayalam", "Gujarati", "Marathi", "Odia", "Nepali", "Sinhala",
    "Chinese (Simplified)", "Chinese (Traditional)", "Japanese", "Korean",
    "Thai", "Vietnamese", "Indonesian", "Malay", "Burmese", "Khmer",
    "Lao", "Mongolian",
    "Swahili", "Amharic",
]

st.set_page_config(
    page_title="LexFusion — Law RAG Workflow Automation",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def load_custom_css():
    css_path = os.path.join(os.path.dirname(__file__), "static", "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def apply_theme(dark: bool):
    """
    Inject a complete CSS override block for the active theme.
    We cannot rely on JS data-theme + CSS variables because Streamlit's
    widget internals ignore inherited CSS variables. Instead we inject
    a full hard-coded override block on every render.
    """
    if dark:
        # Dark theme — these are the base styles already in style.css,
        # but we reinforce the most important ones here.
        st.markdown("""
        <style>
        .stApp, .stApp > div, [data-testid="stAppViewContainer"],
        [data-testid="stVerticalBlock"], section.main, .main,
        [data-testid="block-container"] {
            background-color: #030712 !important;
            color: #f3f4f6 !important;
        }
        /* Text elements */
        p, span, label, div, li, td, th, h1, h2, h3, h4, h5, h6 {
            color: #f3f4f6;
        }
        /* Widgets */
        .stTextInput input, .stTextArea textarea, .stSelectbox select,
        [data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea {
            background-color: rgba(17,24,39,0.6) !important;
            color: #f3f4f6 !important;
            border-color: rgba(255,255,255,0.1) !important;
        }
        /* Selectbox / dropdown */
        [data-testid="stSelectbox"] > div > div {
            background-color: rgba(17,24,39,0.6) !important;
            color: #f3f4f6 !important;
        }
        /* Expander */
        [data-testid="stExpander"] {
            background-color: rgba(17,24,39,0.4) !important;
            border-color: rgba(255,255,255,0.07) !important;
        }
        /* Sliders */
        [data-testid="stSlider"] label { color: #f3f4f6 !important; }
        /* Chat input */
        [data-testid="stChatInput"] textarea {
            background-color: rgba(17,24,39,0.6) !important;
            color: #f3f4f6 !important;
        }
        /* Markdown */
        .stMarkdown, .stMarkdown p, .stMarkdown li { color: #e5e7eb !important; }
        /* HR */
        hr { border-color: rgba(255,255,255,0.08) !important; }
        </style>
        """, unsafe_allow_html=True)
    else:
        # Light theme — fully override every Streamlit dark default
        st.markdown("""
        <style>
        /* ── Full-page light background ── */
        html, body,
        .stApp, .stApp > div,
        [data-testid="stAppViewContainer"],
        [data-testid="stVerticalBlock"],
        section.main, .main,
        [data-testid="block-container"],
        [data-testid="stMainBlockContainer"],
        .block-container,
        [data-testid="stBottom"],
        [data-testid="stStatusWidget"] {
            background-color: #f8f6f0 !important;
            background-image: none !important;
            color: #1a1a2e !important;
        }

        /* ── All text ── */
        p, span, div, li, td, th, a,
        h1, h2, h3, h4, h5, h6,
        label, small, strong, em,
        .stMarkdown, .stMarkdown p,
        .stMarkdown li, .stMarkdown span,
        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
            color: #1a1a2e !important;
        }

        /* ── Navbar ── */
        .top-navbar {
            background: rgba(248,246,240,0.97) !important;
            border-bottom-color: rgba(0,0,0,0.1) !important;
        }

        /* ── Inputs ── */
        .stTextInput input,
        .stTextArea textarea,
        [data-testid="stTextInput"] input,
        [data-testid="stTextArea"] textarea,
        [data-testid="stChatInput"] textarea {
            background-color: #ffffff !important;
            color: #1a1a2e !important;
            border-color: rgba(0,0,0,0.15) !important;
        }

        /* ── Selectbox ── */
        [data-testid="stSelectbox"] > div > div,
        [data-testid="stSelectbox"] * {
            background-color: #ffffff !important;
            color: #1a1a2e !important;
            border-color: rgba(0,0,0,0.15) !important;
        }

        /* ── Expander ── */
        [data-testid="stExpander"],
        [data-testid="stExpander"] > div,
        [data-testid="stExpanderDetails"] {
            background-color: #ffffff !important;
            border-color: rgba(0,0,0,0.1) !important;
            color: #1a1a2e !important;
        }
        [data-testid="stExpander"] summary,
        [data-testid="stExpander"] summary * {
            color: #1a1a2e !important;
        }

        /* ── Buttons ── */
        .stButton > button[kind="secondary"] {
            background-color: #ffffff !important;
            color: #1a1a2e !important;
            border-color: rgba(0,0,0,0.2) !important;
        }
        .stButton > button[kind="secondary"]:hover {
            background-color: #f0ede4 !important;
        }

        /* ── File uploader ── */
        [data-testid="stFileUploader"],
        [data-testid="stFileUploader"] > div,
        [data-testid="stFileDropzoneInstructions"],
        [data-testid="stFileUploaderDropzone"] {
            background-color: #ffffff !important;
            color: #1a1a2e !important;
            border-color: rgba(0,0,0,0.15) !important;
        }
        [data-testid="stFileUploader"] span,
        [data-testid="stFileUploader"] small,
        [data-testid="stFileUploader"] p {
            color: #4b5563 !important;
        }

        /* ── Slider ── */
        [data-testid="stSlider"] label,
        [data-testid="stSlider"] p {
            color: #1a1a2e !important;
        }

        /* ── Alert / success / error boxes ── */
        [data-testid="stAlert"],
        div[role="alert"] {
            background-color: #ffffff !important;
            color: #1a1a2e !important;
        }

        /* ── Status widget ── */
        [data-testid="stStatusWidget"],
        [data-testid="stStatusWidget"] * {
            background-color: #f0ede4 !important;
            color: #1a1a2e !important;
        }

        /* ── Chat message ── */
        [data-testid="stChatMessage"],
        [data-testid="stChatMessage"] > div {
            background-color: #ffffff !important;
            color: #1a1a2e !important;
        }

        /* ── Custom glass cards for light mode ── */
        .glass-card {
            background: rgba(255,255,255,0.9) !important;
            border-color: rgba(0,0,0,0.08) !important;
            color: #1a1a2e !important;
        }
        .glass-card p, .glass-card span, .glass-card div {
            color: #374151 !important;
        }
        .advocate-card {
            background: rgba(255,255,255,0.85) !important;
            color: #374151 !important;
        }

        /* ── HR ── */
        hr { border-color: rgba(0,0,0,0.1) !important; }

        /* ── Scrollbar ── */
        ::-webkit-scrollbar-track { background: rgba(0,0,0,0.04) !important; }
        ::-webkit-scrollbar-thumb { background: rgba(160,124,40,0.3) !important; }

        /* ── Gold text in light mode ── */
        .gold-text { color: #a07c28 !important; text-shadow: none !important; }
        .round-label { color: #a07c28 !important; }
        .navbar-brand { color: #a07c28 !important; text-shadow: none !important; }

        /* ── Column backgrounds ── */
        [data-testid="column"],
        [data-testid="stHorizontalBlock"] {
            background-color: transparent !important;
        }
        </style>
        """, unsafe_allow_html=True)


def main():
    load_custom_css()

    # ── Session defaults ──────────────────────────────────────────────────────
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = True
    if "app_mode" not in st.session_state:
        st.session_state.app_mode = "chat"
    if "selected_language" not in st.session_state:
        st.session_state.selected_language = "English"

    # Apply theme on every render
    apply_theme(st.session_state.dark_mode)

    # ── Initialize API client ─────────────────────────────────────────────────
    if "api_client" not in st.session_state:
        with st.spinner("🏛️ Initializing LexFusion — loading embedding model..."):
            st.session_state.api_client = LexFusionAPIClient()
    client: LexFusionAPIClient = st.session_state.api_client

    # ── Stats for navbar ──────────────────────────────────────────────────────
    stats = client.get_stats()
    chunk_count = stats.get("chunk_count", 0)
    mode_dot   = "🟡" if client.local_mode else "🟢"
    mode_label = "LOCAL" if client.local_mode else "API"
    theme_icon = "🌙" if st.session_state.dark_mode else "☀️"
    theme_label = "Dark" if st.session_state.dark_mode else "Light"

    # ── Top Navbar (pure HTML — rendered first so it sits above everything) ───
    chat_active    = "active" if st.session_state.app_mode == "chat"    else ""
    debate_active  = "active" if st.session_state.app_mode == "debate"  else ""
    upload_active  = "active" if st.session_state.app_mode == "upload"  else ""

    navbar_text_color = "#1a1a2e" if not st.session_state.dark_mode else "#f3f4f6"
    gold = "#a07c28" if not st.session_state.dark_mode else "#c9a84c"

    st.markdown(
        f"""
        <div class="top-navbar" id="lexfusion-navbar">
            <span class="navbar-brand">⚖️ LEXFUSION</span>
            <div class="navbar-divider"></div>
            <span style="font-size:0.72rem; color:var(--text-muted); letter-spacing:1px; text-transform:uppercase;">
                Legal RAG Chamber
            </span>
            <div class="navbar-divider"></div>
            <!-- Navigation pills rendered via Streamlit buttons below -->
            <span id="nav-placeholder" style="display:flex; gap:8px; align-items:center;">
            </span>
            <span style="margin-left:auto; display:flex; align-items:center; gap:12px;">
                <span style="
                    background: rgba(255,255,255,0.04);
                    border: 1px solid var(--border-subtle);
                    border-radius: 999px;
                    padding: 3px 10px;
                    font-size: 0.7rem;
                    color: {'#f59e0b' if client.local_mode else '#10b981'};
                    font-weight: 600;
                    letter-spacing: 0.5px;
                ">{mode_dot} {mode_label}</span>
                <span style="
                    background: rgba(255,255,255,0.04);
                    border: 1px solid var(--border-subtle);
                    border-radius: 999px;
                    padding: 3px 10px;
                    font-size: 0.7rem;
                    color: {'#10b981' if chunk_count > 0 else '#f59e0b'};
                    font-weight: 600;
                ">{'🟢' if chunk_count > 0 else '🟡'} {chunk_count:,} chunks</span>
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Horizontal control row (nav + language + theme toggle) ────────────────
    nav_col, lang_col, theme_col = st.columns([3, 2, 1])

    with nav_col:
        c1, c2 = st.columns(2)
        with c1:
            if st.button(
                "💬 Chat Assistant",
                use_container_width=True,
                type="primary" if st.session_state.app_mode == "chat" else "secondary",
            ):
                st.session_state.app_mode = "chat"
                st.rerun()
        with c2:
            if st.button(
                "⚖️ Debate Chamber",
                use_container_width=True,
                type="primary" if st.session_state.app_mode == "debate" else "secondary",
            ):
                st.session_state.app_mode = "debate"
                st.rerun()

    with lang_col:
        st.selectbox(
            "🌐 Language",
            options=SUPPORTED_LANGUAGES,
            index=SUPPORTED_LANGUAGES.index(st.session_state.selected_language),
            key="selected_language",
            label_visibility="visible",
        )

    with theme_col:
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        if st.button(f"{theme_icon} {theme_label}", use_container_width=True):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()

    st.markdown(
        "<hr style='border-color: var(--border-subtle); margin: 4px 0 20px 0;' />",
        unsafe_allow_html=True,
    )

    # ── Document ingestion expander (below nav bar) ───────────────────────────
    stats = client.get_stats()
    chunk_count = stats.get("chunk_count", 0)
    store_label = f"🟢 {chunk_count:,} chunks indexed" if chunk_count > 0 else "🟡 No documents — upload PDFs to get started"

    with st.expander(f"📥 Ingest Documents  ·  {store_label}", expanded=(chunk_count == 0)):
        uploaded_files = st.file_uploader(
            "Upload Legal PDFs (contracts, rulings, briefs)",
            type=["pdf"],
            accept_multiple_files=True,
            label_visibility="collapsed",
        )
        if uploaded_files:
            for file in uploaded_files:
                if f"uploaded_{file.name}" not in st.session_state:
                    with st.spinner(f"Ingesting {file.name}..."):
                        res = client.upload_document(file.name, file.read())
                        if res.get("status") == "success":
                            chunks = res.get("chunks_added", 0)
                            pages  = res.get("pages_extracted", "?")
                            st.success(f"✅ **{file.name}** — {pages} pages → {chunks} chunks indexed")
                            st.session_state[f"uploaded_{file.name}"] = True
                        else:
                            st.error(f"❌ Ingestion failed: {res.get('message', 'Unknown error')}")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    if st.session_state.app_mode == "chat":
        render_chat_page(client)
    else:
        render_debate_page(client)


main()
