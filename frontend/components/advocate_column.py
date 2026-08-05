"""
LexFusion Advocate Column Component
====================================
Static (non-animated) fallback renderer for debate rounds.
Used on re-renders after the initial animated playback has completed.
"""

from __future__ import annotations

import html
import streamlit as st


def render_debate_rounds(history: list[dict]):
    """Renders all debate rounds statically (no animation delays)."""
    if not history:
        st.info("No debate history available.")
        return

    st.markdown("### 🏛️ Courtroom Debate Logs")

    # Group by round number
    rounds: dict[int, list[dict]] = {}
    for entry in history:
        r_num = entry.get("round", 1)
        rounds.setdefault(r_num, []).append(entry)

    for r_num in sorted(rounds.keys()):
        st.markdown(
            f"""
            <div style="text-align:center; margin:28px 0 16px;">
                <span class="round-label">⚔️ &nbsp; DEBATE ROUND {r_num} &nbsp; ⚔️</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)

        with col1:
            pros = next((e for e in rounds[r_num] if e.get("advocate") == "A"), None)
            if pros:
                safe_arg = html.escape(pros.get("argument", ""))
                st.markdown(
                    f"""
                    <div class="glass-card advocate-card advocate-prosecution advocate-enter-left">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                            <span style="font-weight:700; color:#f59e0b; font-size:0.95rem;">
                                🛡️ Advocate A
                            </span>
                            <span class="status-badge badge-prosecution">PROSECUTION</span>
                        </div>
                        <p style="font-size:0.95rem; line-height:1.7; color:var(--prose-color); white-space:pre-wrap;">{safe_arg}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    "<div class='typing-indicator'>Prosecution argument missing.</div>",
                    unsafe_allow_html=True,
                )

        with col2:
            defence = next((e for e in rounds[r_num] if e.get("advocate") == "B"), None)
            if defence:
                safe_arg = html.escape(defence.get("argument", ""))
                st.markdown(
                    f"""
                    <div class="glass-card advocate-card advocate-defence advocate-enter-right">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                            <span style="font-weight:700; color:#3b82f6; font-size:0.95rem;">
                                ⚖️ Advocate B
                            </span>
                            <span class="status-badge badge-defence">DEFENCE</span>
                        </div>
                        <p style="font-size:0.95rem; line-height:1.7; color:var(--prose-color); white-space:pre-wrap;">{safe_arg}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    "<div class='typing-indicator'>Defence argument missing.</div>",
                    unsafe_allow_html=True,
                )
