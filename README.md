# ⚖️ LexFusion — AI-Powered Legal Research & Adversarial Debate Platform

> **Upload a legal document. Ask a question. Watch two AI lawyers debate it. Get a judge's ruling in under 30 seconds.**

[![Streamlit](https://img.shields.io/badge/Built%20with-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-6366F1)](https://langchain-ai.github.io/langgraph/)
[![Groq](https://img.shields.io/badge/LLM-Groq%20llama--3.3--70b-F59E0B)](https://console.groq.com)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## 📌 What is LexFusion?

LexFusion is a full-stack AI legal research platform with two core capabilities:

| Mode | What it does |
|---|---|
| 💬 **Chat Assistant** | Ask plain-English questions about your uploaded legal documents. Get structured answers with exact citations — no hallucination. |
| ⚖️ **Cross-Examine Debate** | Two AI advocates (Prosecution vs Defence) argue multiple rounds on both sides of a legal question. A neutral AI Judge delivers a final ruling with a confidence score. |

Every response is **grounded exclusively in documents you upload**. The AI is explicitly forbidden from inventing facts, case names, or clauses.

---

## 🎯 Key Features

- **RAG Pipeline** — PDF → extract → chunk → embed → semantic vector search
- **Adversarial LangGraph** — stateful multi-round debate graph with conditional routing
- **50 Languages** — full debate in Hindi, Arabic, French, or any of 50 supported languages
- **Dark / Light Theme** — toggleable with animated transitions
- **Top Navbar UI** — clean horizontal layout replacing the traditional sidebar
- **Animated Debate Reveal** — arguments appear one by one, live, with slide-in animations
- **Streamlit Cloud ready** — zero-server deployment, runs entirely in-process
- **Dual mode** — auto-detects FastAPI backend if running, falls back to local-direct mode

---

## 🏗️ Architecture

```
USER
 │  uploads PDF + types question
 ▼
INGESTION PIPELINE
 ├─ PyMuPDF          → extract text page-by-page
 ├─ LangChain        → split into 800-char overlapping chunks
 ├─ HuggingFace      → embed each chunk (all-MiniLM-L6-v2, 384-dim)
 └─ ChromaDB         → store vectors in-memory

RETRIEVAL (RAG)
 ├─ embed question with same model
 ├─ ChromaDB similarity search → top-k chunks
 └─ format as context string with source citations

         ┌──────────────┬──────────────────────┐
         ▼              ▼
   CHAT MODE       DEBATE MODE (LangGraph)
   Groq LLM        ┌─ Advocate A  (Prosecution)
   single answer   ├─ Advocate B  (Defence)
                   ├─ [loop N rounds]
                   └─ Judge → ruling + confidence score

STREAMLIT FRONTEND
 ├─ Top navbar (Chat | Debate | Language | Theme)
 ├─ Animated argument reveal (slide-in per advocate)
 └─ Confidence gauge (Plotly)
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| UI | Streamlit | Python-native web app |
| Styling | Custom CSS + CSS variables | Dark/light theme, animations |
| PDF Reading | PyMuPDF (fitz) | Page-by-page text extraction |
| Chunking | LangChain Text Splitters | 800-char chunks, 150-char overlap |
| Embeddings | HuggingFace `all-MiniLM-L6-v2` | Local semantic embeddings, no API |
| Vector DB | ChromaDB (EphemeralClient) | In-memory fast similarity search |
| LLM | Groq `llama-3.3-70b-versatile` | ~500 tok/s inference, free tier |
| Orchestration | LangGraph (StateGraph) | Multi-round debate graph |
| API (optional) | FastAPI + Uvicorn | Production server mode |
| Validation | Pydantic v2 | Strict I/O schema enforcement |
| Config | python-dotenv | Secure API key management |

---

## 📁 Project Structure

```
LexFusion-share/
├── frontend/
│   ├── app.py                    # Main Streamlit entry point (top navbar, theme toggle)
│   ├── pages/
│   │   ├── chat.py               # Chat Assistant page
│   │   └── debate.py             # Cross-Examine Debate page (animated)
│   ├── components/
│   │   ├── advocate_column.py    # Debate round renderer (static fallback)
│   │   └── answer_card.py        # Source cards, synthesis card, confidence gauge
│   ├── utils/
│   │   └── api_client.py         # Smart client (API mode ↔ local direct mode)
│   └── static/
│       └── style.css             # Full CSS with dark/light theme variables
│
├── backend/
│   ├── __init__.py               # ingest_pdf() and search_documents() public API
│   ├── main.py                   # FastAPI server (optional, local deployment)
│   ├── ingestion/
│   │   ├── extract.py            # PyMuPDF PDF text extractor
│   │   └── chunk.py              # LangChain text splitter
│   ├── retrieval/
│   │   ├── embed.py              # HuggingFace embedding singleton
│   │   └── vector_store.py       # ChromaDB in-memory vector store wrapper
│   └── schemas/
│       └── models.py             # FastAPI Pydantic request/response models
│
├── agents/
│   ├── __init__.py               # Public exports
│   ├── generate.py               # generate_answer() and run_debate() entry points
│   ├── debate_graph.py           # LangGraph StateGraph — debate orchestration
│   ├── schemas.py                # DebateState TypedDict + response Pydantic models
│   └── prompts/
│       ├── advocate_a_prompt.py  # Prosecution system prompt (IRAC structure)
│       ├── advocate_b_prompt.py  # Defence system prompt (challenge + rebut)
│       └── synthesis_prompt.py   # Judge system prompt (neutral ruling + confidence)
│
├── .streamlit/
│   ├── config.toml               # Streamlit config (no sidebar nav, port 8501)
│   └── secrets.toml.example      # Template for Streamlit Cloud secrets
│
├── requirements.txt              # All dependencies (Streamlit Cloud deploy)
├── .env.example                  # Environment variable template
└── docs/
    └── api_contract.md           # FastAPI endpoint documentation
```

---

## 🚀 Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/anagha16543/fusion.git
cd fusion
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set your Groq API key
```bash
cp .env.example .env
# Edit .env and add your key:
# GROQ_API_KEY=your_key_here
# Get a free key at https://console.groq.com
```

### 4. Run the app
```bash
streamlit run frontend/app.py
```

Open **http://localhost:8501** in your browser.

---

## ☁️ Streamlit Cloud Deployment

1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app
3. Set **Main file path**: `frontend/app.py`
4. In **Secrets**, add:
   ```toml
   GROQ_API_KEY = "your_key_here"
   ```
5. Deploy — no server, no Docker, no setup needed

---

## ⚙️ Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `GROQ_API_KEY` | ✅ Yes | — | Groq API key ([get free key](https://console.groq.com)) |
| `GROQ_MODEL` | No | `llama-3.3-70b-versatile` | Groq model to use |
| `LLM_TEMPERATURE` | No | `0.3` | LLM temperature (0 = deterministic) |
| `MAX_DEBATE_ROUNDS` | No | `2` | Default number of debate rounds (1–3) |
| `LEXFUSION_API_URL` | No | `http://localhost:8000` | FastAPI backend URL (local mode only) |

---

## 🔄 How the Debate Works

```
User question: "Is the vendor liable for a data breach caused by a third-party API?"

Round 1
  🛡️ Advocate A (Prosecution):
     "Section 14.1 imposes strict indemnification. The vendor is liable."

  ⚖️ Advocate B (Defence):
     "Section 8.2 excludes third-party liability. The claim must fail."

Round 2
  🛡️ Advocate A: "Section 8.2's carve-out is void under Section 3..."
  ⚖️ Advocate B: "The prosecution misreads Section 3. The exclusion stands..."

⚖️ Judge Ruling:
  "The defence position is better supported. Section 8.2 clearly excludes
   indirect damages from third-party causes. However, Section 14.1 creates
   ambiguity a court could exploit.
   Confidence Score: 72% — ambiguity in definitions reduces certainty."
```

Arguments are revealed **one by one** with slide-in animations — Advocate A first, then Advocate B, then the Judge — so you can follow the debate live.

---

## 🌐 Supported Languages

LexFusion supports **50 languages** — every agent (Advocate A, B, and Judge) responds entirely in the selected language:

English · Spanish · French · German · Italian · Dutch · Portuguese · Russian · Polish · Swedish · Norwegian · Danish · Finnish · Greek · Romanian · Czech · Hungarian · Slovak · Croatian · Ukrainian · Arabic · Hebrew · Turkish · Kazakh · Hindi · Bengali · Urdu · Punjabi · Tamil · Telugu · Kannada · Malayalam · Gujarati · Marathi · Odia · Nepali · Sinhala · Chinese (Simplified) · Chinese (Traditional) · Japanese · Korean · Thai · Vietnamese · Indonesian · Malay · Burmese · Khmer · Lao · Mongolian · Swahili · Amharic

---

## 📊 Numbers at a Glance

| Metric | Value |
|---|---|
| Supported languages | 50 |
| Debate rounds | 1 – 3 (configurable per query) |
| Chunks per 10-page PDF | ~40 – 80 |
| Embedding model size | ~90 MB (downloaded once) |
| LLM inference speed | ~500 tokens/sec (Groq) |
| Average debate completion | 15 – 25 seconds |
| Python modules | 15 |

---

## 🔒 Security Notes

- `.env` is in `.gitignore` — your API key is never committed
- All LLM-generated content injected into HTML is `html.escape()`d — no XSS
- Pydantic v2 validates every request and response — no unvalidated input reaches the LLM
- ChromaDB runs in-memory (EphemeralClient) — no data persists between sessions

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">
  <b>Built for Hackathon 2026 &nbsp;·&nbsp; Team LexFusion</b>
</div>
