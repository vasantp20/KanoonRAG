# KanoonRAG

**AI-Powered Legal Research Assistant for Indian Matrimonial Disputes**

KanoonRAG is a Retrieval-Augmented Generation (RAG) system that helps lawyers cross-verify case files and prepare accurate legal documents for matrimonial disputes, with citations sourced from a pre-built Indian Kanoon case law corpus.

## Features

- 📋 **Client Management** — Register clients with demographic details and create cases
- 📁 **Case File Upload** — Upload PDF/DOCX case files, auto-chunked and embedded for RAG
- 🔍 **AI Research Assistant** — Query 500+ pre-indexed matrimonial case precedents with citation-backed answers
- 📄 **Document Generation** — Auto-generate case briefs, legal notices, and analysis memos in DOCX format
- 📚 **Case Law Browser** — Browse and search the pre-fetched corpus by category, court, and date
- 🔒 **Multi-Tenant Auth** — JWT-authenticated access with tenant-isolated data

## Case Categories

| Category | Key Statutes |
|---|---|
| Divorce (Cruelty Grounds) | HMA §13(1)(ia) |
| Maintenance | CrPC §125, HMA §24-25 |
| Child Custody | GWA §6-7, HMA §26 |
| Domestic Violence | DV Act 2005 |
| Dowry / 498A | IPC §498A, Dowry Prohibition Act |

## Tech Stack

| Component | Technology |
|---|---|
| Backend | FastAPI (Python) |
| Frontend | Streamlit |
| LLM | Groq (LLaMA 3.3 70B, free tier) |
| Embeddings | sentence-transformers (BAAI/bge-small-en-v1.5, local) |
| Vector Store | ChromaDB |
| Database | SQLite (async via aiosqlite) |
| Document Processing | PyMuPDF, python-docx |
| Case Law Source | Indian Kanoon API (pre-fetched, offline) |

## Setup

### 1. Clone and Install

```bash
git clone <repository-url>
cd KanoonRAG
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your keys:
# - GROQ_API_KEY (get from https://console.groq.com)
# - KANOON_API_TOKEN (for the one-time seed script)
# - JWT_SECRET_KEY (any random string)
```

### 3. Initialize Database

```bash
python scripts/init_db.py
```

### 4. Seed Case Law Corpus (One-Time)

```bash
python scripts/seed_kaggle.py
```

This will:
- Scan the Kaggle dataset PDFs for matrimonial keywords
- Process and chunk each matching document
- Generate embeddings locally (takes ~10-15 min on CPU for 500 cases)
- Store everything in ChromaDB + SQLite

### 5. Run the Application

In two separate terminals:

```bash
# Terminal 1: Backend API
uvicorn app.main:app --reload --port 8000
python3 -m uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
streamlit run streamlit_app.py --server.port 8501
```

Open http://localhost:8501 in your browser.

## Project Structure

```
KanoonRAG/
├── app/
│   ├── api/routes/       # FastAPI endpoints (auth, clients, cases, query, documents, kanoon)
│   ├── core/             # Business logic (auth, RAG engine, embeddings, vector store, doc generator)
│   └── db/               # SQLAlchemy models and database
├── frontend/
│   ├── streamlit_app.py  # Main Streamlit entry
│   └── pages/            # Multi-page Streamlit app
├── scripts/
│   ├── init_db.py        # Database initialization
│   └── seed_kanoon.py    # One-time corpus builder
├── data/
│   ├── uploads/          # User-uploaded files
│   ├── kanoon_cache/     # Cached Kanoon API responses
│   └── chroma_db/        # ChromaDB persistent storage
├── config.py             # Central configuration
└── requirements.txt
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Login and get JWT |
| GET | `/auth/me` | Get current user |
| CRUD | `/clients/` | Client management |
| CRUD | `/cases/` | Case management |
| POST | `/cases/{id}/upload` | Upload case files |
| POST | `/query/` | RAG query |
| POST | `/documents/generate` | Generate DOCX |
| GET | `/documents/{id}/download` | Download DOCX |
| GET | `/kanoon/browse` | Browse case law corpus |

## Disclaimer

> This system is designed as a portfolio project and research tool. Generated documents are AI-assisted drafts and must be reviewed by a qualified legal professional before any official use.

## License

MIT
