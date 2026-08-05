"""
LexFusion Cross-Examine Debate Page
====================================
Animated courtroom debate: arguments are revealed one by one
(Advocate A ΓåÆ Advocate B ΓåÆ next round ΓåÆ ... ΓåÆ Judge ruling).
"""

from __future__ import annotations

import os
import sys
import time
import html

_here = os.path.dirname(os.path.abspath(__file__))
_frontend = os.path.abspath(os.path.join(_here, ".."))
_project_root = os.path.abspath(os.path.join(_frontend, ".."))
for _p in (_project_root, _frontend):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import streamlit as st
from utils.api_client import LexFusionAPIClient
from components.answer_card import render_synthesis_card, render_source_cards

# ΓöÇΓöÇ Animated argument card HTML builders ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

def _prosecution_card(argument: str, round_num: int) -> str:
    safe = html.escape(argument)
    return f"""
    <div class="glass-card advocate-card advocate-prosecution advocate-enter-left"
         style="animation-delay:0.05s">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
            <span style="font-weight:700; color:#f59e0b; font-size:0.95rem;">
                ≡ƒ¢í∩╕Å Advocate A &nbsp;<span style="font-size:0.78rem; color:var(--text-muted);">Round {round_num}</span>
            </span>
            <span class="status-badge badge-prosecution">PROSECUTION</span>
        </div>
        <p style="font-size:0.95rem; line-height:1.7; color:var(--prose-color); white-space:pre-wrap;">{safe}</p>
    </div>"""


def _defence_card(argument: str, round_num: int) -> str:
    safe = html.escape(argument)
    return f"""
    <div class="glass-card advocate-card advocate-defence advocate-enter-right"
         style="animation-delay:0.05s">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
            <span style="font-weight:700; color:#3b82f6; font-size:0.95rem;">
                ΓÜû∩╕Å Advocate B &nbsp;<span style="font-size:0.78rem; color:var(--text-muted);">Round {round_num}</span>
            </span>
            <span class="status-badge badge-defence">DEFENCE</span>
        </div>
        <p style="font-size:0.95rem; line-height:1.7; color:var(--prose-color); white-space:pre-wrap;">{safe}</p>
    </div>"""


def _waiting_card(side: str) -> str:
    label = "Prosecution" if side == "A" else "Defence"
    icon  = "≡ƒ¢í∩╕Å" if side == "A"  else "ΓÜû∩╕Å"
    cls   = "advocate-prosecution" if side == "A" else "advocate-defence"
    return f"""
    <div class="glass-card advocate-card {cls}" style="opacity:0.6;">
        <div style="display:flex; align-items:center; gap:10px; color:var(--text-secondary);">
            <span>{icon} {label}</span>
            <div class="dot-flashing"><span></span><span></span><span></span></div>
        </div>
    </div>"""


def _round_header(r_num: int) -> str:
    return f"""
    <div class="round-header-enter" style="text-align:center; margin:28px 0 16px;">
        <span class="round-label">ΓÜö∩╕Å &nbsp; DEBATE ROUND {r_num} &nbsp; ΓÜö∩╕Å</span>
    </div>"""


# ΓöÇΓöÇ Animated playback ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

def _animate_debate(history: list[dict], synthesis: str, confidence: int, sources: list[dict]):
    """
    Streams the debate argument-by-argument with short delays between reveals.
    After all rounds, reveals the Judge ruling with a special entrance animation.
    """
    # Group entries by round
    rounds: dict[int, dict] = {}
    for entry in history:
        r = entry.get("round", 1)
        if r not in rounds:
            rounds[r] = {}
        rounds[r][entry.get("advocate")] = entry.get("argument", "")

    st.markdown("### ≡ƒÅ¢∩╕Å Courtroom Debate ΓÇö Live Session")

    # One placeholder per round-side combination so we can update in place
    for r_num in sorted(rounds.keys()):
        # Round header
        header_slot = st.empty()
        header_slot.markdown(_round_header(r_num), unsafe_allow_html=True)
        time.sleep(0.4)

        col_a, col_b = st.columns(2)

        # ΓöÇΓöÇ Advocate A speaks first ΓöÇΓöÇ
        with col_a:
            slot_a = st.empty()
            slot_a.markdown(_waiting_card("A"), unsafe_allow_html=True)

        with col_b:
            slot_b = st.empty()
            slot_b.markdown(_waiting_card("B"), unsafe_allow_html=True)

        # Reveal A after a short pause (simulates thinking)
        time.sleep(1.0)
        arg_a = rounds[r_num].get("A", "")
        with col_a:
            slot_a.markdown(_prosecution_card(arg_a, r_num), unsafe_allow_html=True)

        # Reveal B after A
        time.sleep(1.2)
        arg_b = rounds[r_num].get("B", "")
        with col_b:
            slot_b.markdown(_defence_card(arg_b, r_num), unsafe_allow_html=True)

        # Pause between rounds
        if r_num < max(rounds.keys()):
            time.sleep(0.8)

    # ΓöÇΓöÇ Judge ruling entrance ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    st.markdown(
        "<hr style='border-color:rgba(255,255,255,0.08); margin:30px 0;' />",
        unsafe_allow_html=True,
    )

    judge_placeholder = st.empty()
    judge_placeholder.markdown(
        """
        <div class="glass-card" style="border-color:rgba(139,92,246,0.3); text-align:center; padding:30px; opacity:0.5;">
            <span class="court-title" style="color:#a78bfa; font-size:1.2rem;">
                ΓÜû∩╕Å Presiding Judge deliberating...
            </span>
            <div class="dot-flashing" style="justify-content:center; display:flex; margin-top:12px;">
                <span></span><span></span><span></span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    time.sleep(1.5)
    judge_placeholder.empty()

    # Render the real synthesis card (with animation class applied via CSS)
    st.markdown(
        '<div class="judge-enter">',
        unsafe_allow_html=True,
    )
    render_synthesis_card(synthesis=synthesis, confidence_score=confidence)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)
    render_source_cards(sources)


# ΓöÇΓöÇ Page render ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

def render_debate_page(client: LexFusionAPIClient):
    """Renders the adversarial debate page."""
    language = st.session_state.get("selected_language", "English")
    lang_flag = "≡ƒîì" if language != "English" else "ΓÜû∩╕Å"

    st.markdown(
        f"""
        <div style="margin-bottom:22px;">
            <h1 class="court-title" style="font-size:2.2rem; margin-bottom:5px;">
                ≡ƒÅ¢∩╕Å Cross-Examine <span class="gold-text">Debate Chamber</span>
            </h1>
            <p style="color:var(--text-secondary); font-size:1rem;">
                Adversarial AI debate between Prosecution and Defence ΓÇö arguments revealed live, one by one.
            </p>
            <span style="
                background:rgba(201,168,76,0.1);
                border:1px solid rgba(201,168,76,0.25);
                border-radius:999px;
                padding:3px 12px;
                font-size:0.78rem;
                color:var(--gold);
                font-weight:600;
            ">{lang_flag} All advocates debating in: {language}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ΓöÇΓöÇ Inline settings bar ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    sc1, sc2 = st.columns([1, 1])
    with sc1:
        debate_rounds = st.slider("ΓÜö∩╕Å Debate Rounds", min_value=1, max_value=3, value=2)
    with sc2:
        top_k = st.slider("≡ƒöì Evidence Chunks (Top K)", min_value=3, max_value=10, value=5)

    # ΓöÇΓöÇ Query input ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    st.markdown("### ≡ƒô£ File an Argument")
    user_query = st.text_area(
        "Define the legal issue/dispute to cross-examine:",
        placeholder="e.g., Is the vendor liable for damages if a data breach occurs due to a third-party API outage?",
        height=90,
        key="debate_query_input",
    )

    start_debate = st.button("ΓÜû∩╕Å Convene Courtroom", use_container_width=True, type="primary")

    if start_debate:
        if not user_query.strip():
            st.warning("Please provide a legal query first.")
            return

        # Clear previous debate so animation reruns fresh
        st.session_state.pop("active_debate", None)

        with st.status(
            f"≡ƒÅ¢∩╕Å Court is in session ΓÇö running Agentic Graph in {language}...",
            expanded=True,
        ) as status:
            status.update(label=f"Advocates preparing arguments in {language}...", state="running")

            response = client.query(
                query=user_query,
                debate_mode=True,
                top_k=top_k,
                max_rounds=debate_rounds,
                language=language,
            )

            if response.get("status") == "complete" or "synthesis" in response:
                status.update(label="All arguments collected. Starting animated playback...", state="complete")
                st.session_state.active_debate = response
                st.session_state.active_debate_language = language
            else:
                status.update(label="Court session errored.", state="error")
                st.error(f"Court session aborted: {response.get('error_message', 'Execution failed.')}")
                return

    # ΓöÇΓöÇ Animated debate display ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    if "active_debate" in st.session_state:
        res = st.session_state.active_debate
        debate_lang = st.session_state.get("active_debate_language", "English")

        if debate_lang != language:
            st.info(
                f"Γä╣∩╕Å This debate was in **{debate_lang}**. "
                f"Press 'ΓÜû∩╕Å Convene Courtroom' to re-run in **{language}**."
            )

        # Only animate on the first render after a new debate finishes.
        # Use a flag so replay on re-render shows static cards (no delay).
        anim_key = f"_animated_{id(res)}"
        if not st.session_state.get(anim_key):
            st.session_state[anim_key] = True
            _animate_debate(
                history=res.get("argument_history", []),
                synthesis=res.get("synthesis", "Synthesis unavailable."),
                confidence=res.get("confidence_score", 50),
                sources=res.get("source_documents", []),
            )
        else:
            # Static re-render (after Streamlit re-runs due to user interaction)
            from components.advocate_column import render_debate_rounds
            render_debate_rounds(res.get("argument_history", []))
            st.markdown(
                "<hr style='border-color:rgba(255,255,255,0.08); margin:30px 0;'/>",
                unsafe_allow_html=True,
            )
            render_synthesis_card(
                synthesis=res.get("synthesis", "Synthesis unavailable."),
                confidence_score=res.get("confidence_score", 50),
            )
            st.markdown("<br/>", unsafe_allow_html=True)
            render_source_cards(res.get("source_documents", []))
