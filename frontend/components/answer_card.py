"""
LexFusion Answer Card Component
================================
Renders clean UI cards for answers, sources, disclaimers,
and an animated gauge for confidence scores.
"""

from __future__ import annotations

import streamlit as st
import plotly.graph_objects as go


def render_confidence_gauge(score: int):
    """Renders a beautiful circular gauge using Plotly for AI confidence."""
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            domain={"x": [0, 1], "y": [0, 1]},
            number={"suffix": "%", "font": {"size": 24, "color": "#f3f4f6"}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#9ca3af"},
                "bar": {"color": "#c9a84c"},
                "bgcolor": "rgba(17, 24, 39, 0.5)",
                "borderwidth": 1,
                "bordercolor": "rgba(255, 255, 255, 0.1)",
                "steps": [
                    {"range": [0, 40], "color": "rgba(239, 68, 68, 0.1)"},
                    {"range": [40, 75], "color": "rgba(245, 158, 11, 0.1)"},
                    {"range": [75, 100], "color": "rgba(16, 185, 129, 0.1)"},
                ],
            },
        )
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=10, b=10),
        height=140,
        width=180,
    )

    st.plotly_chart(fig, use_container_width=False, config={"displayModeBar": False})


def render_source_cards(sources: list[dict]):
    """Renders document chunks as glassmorphic cards with expanders."""
    if not sources:
        st.markdown("*No document sources cited.*")
        return

    st.markdown("### 📂 Cited Legal Evidence")
    for idx, doc in enumerate(sources):
        source_name = doc.get("source", "Unknown Document")
        page = doc.get("page", "?")
        chunk_text = doc.get("chunk", "")

        with st.expander(f"📄 Source #{idx+1}: {source_name} (Page {page})"):
            st.markdown(
                f"""
                <div class="glass-card advocate-card" style="margin-top: 5px; margin-bottom: 5px;">
                    <p style="font-style: italic; color: #d1d5db; font-size: 0.95rem;">
                        "{chunk_text}"
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_synthesis_card(synthesis: str, confidence_score: int):
    """Renders the Judge's final synthesis report."""
    st.markdown(
        """
        <div class="glass-card" style="border-color: rgba(139, 92, 246, 0.3);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <span class="court-title" style="font-size: 1.4rem; font-weight: bold; color: #a78bfa;">
                    ⚖️ Presiding Judge Findings
                </span>
                <span class="status-badge badge-judge">RULING DELIVERED</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Split into 2 columns: Ruling text on left, gauge on right
    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown(synthesis)

    with col2:
        st.markdown(
            "<div style='text-align: center; font-weight: 500; font-size: 0.9rem; color: #9ca3af;'>Verdict Certainty</div>",
            unsafe_allow_html=True,
        )
        render_confidence_gauge(confidence_score)
