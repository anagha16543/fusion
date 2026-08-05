import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def build_pdf(filename):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Palette
    PRIMARY = colors.HexColor('#0F172A')   # Navy / Slate 900
    GOLD = colors.HexColor('#C9A84C')      # Court Gold
    SECONDARY = colors.HexColor('#334155') # Slate 700
    BG_LIGHT = colors.HexColor('#F8FAFC')  # Slate 50
    ACCENT_RED = colors.HexColor('#991B1B')# Prosecution Red
    ACCENT_BLUE = colors.HexColor('#1E40AF')# Defence Blue
    
    # Custom Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=PRIMARY,
        spaceAfter=2
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=GOLD,
        spaceAfter=12
    )
    
    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=PRIMARY,
        spaceBefore=12,
        spaceAfter=6
    )
    
    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=SECONDARY,
        spaceAfter=6
    )

    summary_text_style = ParagraphStyle(
        'SummaryText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=colors.white
    )

    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Code'],
        fontName='Courier',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#F8FAFC'),
        spaceAfter=0
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.white
    )

    table_body_style = ParagraphStyle(
        'TableBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=SECONDARY
    )

    story = []

    # ── HEADER ──
    story.append(Paragraph("LexFusion", title_style))
    story.append(Paragraph("AUTONOMOUS MULTI-AGENT LEGAL RAG CHAMBER", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=GOLD, spaceAfter=10))

    # Meta Table
    meta_data = [
        [
            Paragraph("<b>Repository:</b> <font color='#1E40AF'>github.com/anagha16543/fusion</font>", table_body_style),
            Paragraph("<b>Branch:</b> main | <b>Version:</b> v2.4.0", table_body_style),
            Paragraph("<b>Deployment:</b> Streamlit Cloud", table_body_style)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[2.5*inch, 2.5*inch, 2.4*inch])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_LIGHT),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # ── EXECUTIVE SUMMARY CARD ──
    summary_html = """
    <b>Executive Summary:</b><br/>
    <b>LexFusion</b> transforms static legal document analysis into an autonomous, multi-agent courtroom simulation.
    Orchestrated using a <b>LangGraph StateGraph</b>, three specialized AI agents (Prosecution, Defence, and Judge)
    cross-examine legal context, challenge arguments in multi-turn rebuttal loops, eliminate single-shot AI bias,
    and generate grounded legal rulings complete with quantitative confidence scoring.
    """
    summary_table = Table([[Paragraph(summary_html, summary_text_style)]], colWidths=[7.4*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), PRIMARY),
        ('BOX', (0,0), (-1,-1), 1, GOLD),
        ('PADDING', (0,0), (-1,-1), 10),
        ('ROUNDEDCORNERS', [4, 4, 4, 4]),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 10))

    # ── ARCHITECTURE & WORKFLOW ──
    story.append(Paragraph("1. System Architecture & Workflow", h2_style))
    flow_diagram = """[ User Legal Query + Uploaded PDFs ]
       │
       ▼
[ Vector Store RAG Retrieval ] ──► (ChromaDB + SentenceTransformers all-MiniLM-L6-v2)
       │
       ▼
[ LangGraph State Machine Execution ]
 ├── 🔴 Advocate A (Prosecution Node)  ──► Affirmative IRAC argument grounded in context
 ├── 🔵 Advocate B (Defence Node)      ──► Point-by-point rebuttal + Defence case
 └── 🔄 Conditional Round Check Edge   ──► Multi-turn rebuttal loop (1 to 3 Rounds)
       │
       ▼
 ⚖️ Presiding Judge Node (Synthesis)  ──► Neutral ruling + Confidence score (0-100%)
       │
       ▼
[ Streamlit Interactive Chamber UI + Plotly Radar/Gauge + PDF Brief Exporter ]"""
    
    flow_table = Table([[Paragraph(flow_diagram.replace('\n', '<br/>').replace(' ', '&nbsp;'), code_style)]], colWidths=[7.4*inch])
    flow_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#0F172A')),
        ('PADDING', (0,0), (-1,-1), 8),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#334155')),
    ]))
    story.append(flow_table)
    story.append(Spacer(1, 10))

    # ── 3 AI AGENTS DEEP DIVE ──
    story.append(Paragraph("2. Multi-Agent Cross-Examination Engine", h2_style))
    
    agents_data = [
        [
            Paragraph("<b>Agent</b>", table_header_style),
            Paragraph("<b>Role & Perspective</b>", table_header_style),
            Paragraph("<b>Core Function & Methodology</b>", table_header_style)
        ],
        [
            Paragraph("<font color='#991B1B'><b>🔴 Agent 1:<br/>Advocate A</b></font>", table_body_style),
            Paragraph("Prosecution / Plaintiff", table_body_style),
            Paragraph("Constructs affirmative legal arguments using the <b>IRAC</b> framework (Issue, Rule, Application, Conclusion) strictly grounded in retrieved evidence. Pre-empts counterarguments.", table_body_style)
        ],
        [
            Paragraph("<font color='#1E40AF'><b>🔵 Agent 2:<br/>Advocate B</b></font>", table_body_style),
            Paragraph("Defence / Respondent", table_body_style),
            Paragraph("Executes point-by-point rebuttals against Prosecution claims. Identifies evidentiary gaps, procedural issues, or statutory exceptions from retrieved context.", table_body_style)
        ],
        [
            Paragraph("<font color='#92400E'><b>⚖️ Agent 3:<br/>Presiding Judge</b></font>", table_body_style),
            Paragraph("Impartial Judicial Arbiter", table_body_style),
            Paragraph("Synthesizes both positions, evaluates evidence quality, parses a quantitative <b>Confidence Score (0-100%)</b>, highlights strengths/weaknesses, and issues a final binding legal opinion.", table_body_style)
        ]
    ]
    agents_table = Table(agents_data, colWidths=[1.5*inch, 1.6*inch, 4.3*inch])
    agents_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('PADDING', (0,0), (-1,-1), 6),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_LIGHT])
    ]))
    story.append(agents_table)
    story.append(Spacer(1, 10))

    # ── TECH STACK TABLE ──
    story.append(Paragraph("3. Technology Stack Breakdown", h2_style))
    
    tech_data = [
        [
            Paragraph("<b>Category</b>", table_header_style),
            Paragraph("<b>Technologies</b>", table_header_style),
            Paragraph("<b>Implementation Details</b>", table_header_style)
        ],
        [
            Paragraph("<b>Agent Framework</b>", table_body_style),
            Paragraph("LangGraph 0.4.x, LangChain 0.2.x", table_body_style),
            Paragraph("StateGraph execution, state immutability, cycle loop routing.", table_body_style)
        ],
        [
            Paragraph("<b>LLM Inference</b>", table_body_style),
            Paragraph("Groq API (Llama-3.3-70B), Gemini", table_body_style),
            Paragraph("Ultra-fast model inference for multi-agent multi-round debates.", table_body_style)
        ],
        [
            Paragraph("<b>Vector Store & Embed</b>", table_body_style),
            Paragraph("ChromaDB, SentenceTransformers", table_body_style),
            Paragraph("Semantic PDF chunking (`all-MiniLM-L6-v2`) & similarity scoring.", table_body_style)
        ],
        [
            Paragraph("<b>Backend REST API</b>", table_body_style),
            Paragraph("FastAPI, Uvicorn, Pydantic v2", table_body_style),
            Paragraph("Endpoints `/query`, `/upload`, `/health`, `/stats` with strict typing.", table_body_style)
        ],
        [
            Paragraph("<b>Frontend UI</b>", table_body_style),
            Paragraph("Streamlit 1.35+, Plotly 5.20+, CSS3", table_body_style),
            Paragraph("Glassmorphic UI (`#050814`), split-screen debate view, sound FX.", table_body_style)
        ],
        [
            Paragraph("<b>Multilingual Engine</b>", table_body_style),
            Paragraph("Multilingual System Directives", table_body_style),
            Paragraph("Supports <b>50 global languages</b> across all 3 AI agent outputs.", table_body_style)
        ],
        [
            Paragraph("<b>Analytics & Export</b>", table_body_style),
            Paragraph("Plotly Gauges/Radar, Brief Exporter", table_body_style),
            Paragraph("Visual legal strength metrics, match bars, and HTML/PDF brief generator.", table_body_style)
        ]
    ]
    tech_table = Table(tech_data, colWidths=[1.5*inch, 2.1*inch, 3.8*inch])
    tech_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('PADDING', (0,0), (-1,-1), 5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_LIGHT])
    ]))
    story.append(tech_table)
    story.append(Spacer(1, 10))

    # ── KEY HACKATHON INNOVATIONS ──
    story.append(Paragraph("4. Standout Key Innovations", h2_style))
    innovations = [
        "<b>• Dual-Mode Execution:</b> Automatic fallback to in-process local agents when FastAPI server is offline, ensuring 100% uptime on Streamlit Cloud.",
        "<b>• Adversarial Legal Testing:</b> Eliminates single-agent bias by forcing opposing perspectives to battle over retrieved facts.",
        "<b>• Zero-Hallucination Grounding:</b> Agents are constrained to cited document chunks with similarity percentage match bars (`[██████████░] 94%`).",
        "<b>• Interactive Legal Analytics:</b> Plotly Legal Strength Radar Chart & Confidence Radial Meter provide instant executive visibility.",
        "<b>• 50 Global Languages:</b> Full multilingual prompt engineering enables cross-border legal contract cross-examination."
    ]
    for inn in innovations:
        story.append(Paragraph(inn, body_style))
        
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E1'), spaceAfter=8))
    story.append(Paragraph("<font color='#94A3B8' size='8'>LexFusion — github.com/anagha16543/fusion | Generated for Project Presentation & Hackathon Submission</font>", ParagraphStyle('Foot', parent=styles['Normal'], alignment=1)))

    doc.build(story)
    print(f"Successfully generated PDF: {filename}")

if __name__ == "__main__":
    out_pdf = r"C:\Users\Anagha\OneDrive\Documents\LexFusion-share\LexFusion_Project_Summary.pdf"
    build_pdf(out_pdf)
