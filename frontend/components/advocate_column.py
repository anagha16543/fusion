"""
LexFusion Advocate Column Component
====================================
Renders side-by-side debate columns for the Prosecution
and Defence arguments, highlighting active turns.
"""

from __future__ import annotations

import streamlit as st


def render_debate_rounds(history: list[dict]):
    """Renders debate rounds in a responsive split columns layout."""
    if not history:
        st.info("Initiating cross-examination debate rounds...")
        return

    st.markdown("### 🏛️ Courtroom Debate Logs")

    # Group by round number
    rounds: dict[int, list[dict]] = {}
    for entry in history:
        r_num = entry.get("round", 1)
        if r_num not in rounds:
            rounds[r_num] = []
        rounds[r_num].append(entry)

    # Sort rounds
    for r_num in sorted(rounds.keys()):
        st.markdown(
            f"""
            <div style="text-align: center; margin-top: 25px; margin-bottom: 15px;">
                <span style="font-family: 'Cinzel', serif; font-size: 0.95rem; 
                      color: #c9a84c; border-bottom: 1px solid rgba(201, 168, 76, 0.4); 
                      padding: 2px 15px; letter-spacing: 2px;">
                    DEBATE ROUND {r_num}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)

        # Prosecution column
        with col1:
            pros_entry = next((e for e in rounds[r_num] if e.get("advocate") == "A"), None)
            if pros_entry:
                st.markdown(
                    f"""
                    <div class="glass-card advocate-card advocate-prosecution">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <span style="font-weight: 700; color: #f59e0b; font-size: 0.95rem;">
                                🛡️ Advocate A
                            </span>
                            <span class="status-badge badge-prosecution">PROSECUTION</span>
                        </div>
                        <p style="font-size: 0.95rem; line-height: 1.6; color: #e5e7eb;">
                            {pros_entry.get('argument')}
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    """
                    <div class="typing-indicator">Prosecution preparing argument...</div>
                    """,
                    unsafe_allow_html=True,
                )

        # Defence column
        with col2:
            def_entry = next((e for e in rounds[r_num] if e.get("advocate") == "B"), None)
            if def_entry:
                st.markdown(
                    f"""
                    <div class="glass-card advocate-card advocate-defence">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <span style="font-weight: 700; color: #3b82f6; font-size: 0.95rem;">
                                ⚖️ Advocate B
                            </span>
                            <span class="status-badge badge-defence">DEFENCE</span>
                        </div>
                        <p style="font-size: 0.95rem; line-height: 1.6; color: #e5e7eb;">
                            {def_entry.get('argument')}
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    """
                    <div class="typing-indicator">Defence awaiting prosecution argument...</div>
                    """,
                    unsafe_allow_html=True,
                )
