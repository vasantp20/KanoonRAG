"""
KanoonRAG — Central Configuration

All configurable values are defined here. Environment variables override defaults.
Models:
mixtral:8x22b
mistral:7b
gpt-oss:20b

Base URL
http://localhost:11434/

for RunPod:
http://localhost:11435/
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

# Helper to resolve relative env paths to absolute paths
def _resolve_path(env_val, default_path):
    if not env_val:
        return str(default_path)
    p = Path(env_val)
    return str(p.resolve()) if p.is_absolute() else str((BASE_DIR / p).resolve())

UPLOAD_DIR = Path(_resolve_path(os.getenv("UPLOAD_DIR"), DATA_DIR / "uploads"))
KANOON_CACHE_DIR = Path(_resolve_path(os.getenv("KANOON_CACHE_DIR"), DATA_DIR / "kanoon_cache"))
CHROMA_PERSIST_DIR = _resolve_path(os.getenv("CHROMA_PERSIST_DIR"), DATA_DIR / "chroma_db")

# ── Database ───────────────────────────────────────────────────────────────────
env_db_url = os.getenv("DATABASE_URL")
if env_db_url and env_db_url.startswith("sqlite+aiosqlite:///./"):
    # Fix relative sqlite paths
    DATABASE_URL = f"sqlite+aiosqlite:///{BASE_DIR}/{env_db_url.split('sqlite+aiosqlite:///./')[1]}"
else:
    DATABASE_URL = env_db_url or f"sqlite+aiosqlite:///{DATA_DIR / 'kanoonrag.db'}"

# ── Auth ───────────────────────────────────────────────────────────────────────
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24

# ── LLM Configuration ─────────────────────────────────────────────────────────
PRIMARY_LLM = os.getenv("PRIMARY_LLM", "ollama")  # Options: 'ollama', 'groq', 'sarvam'

# ── Sarvam AI LLM ─────────────────────────────────────────────────────────────
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "")
SARVAM_MODEL = os.getenv("SARVAM_MODEL", "sarvam-105b")
SARVAM_BASE_URL = os.getenv("SARVAM_BASE_URL", "https://api.sarvam.ai/v1/chat/completions")

# ── Groq LLM ──────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = "openai/gpt-oss-120b"
GROQ_TEMPERATURE = 0.3
GROQ_MAX_TOKENS = 4096


# ── Ollama Fallback LLM ───────────────────────────────────────────────────────
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11435")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mixtral:8x22b")
OLLAMA_TEMPERATURE = 0.3
OLLAMA_MAX_TOKENS = 4096

# ── Embeddings ─────────────────────────────────────────────────────────────────
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIMENSION = 384

# ── Chunking ──────────────────────────────────────────────────────────────────
CHUNK_SIZE = 2000
CHUNK_OVERLAP = 300

# ── Vector Store ──────────────────────────────────────────────────────────────
KANOON_COLLECTION = "kanoon_matrimonial"
USER_UPLOADS_COLLECTION = "user_uploads"
TOP_K_KANOON = 8
TOP_K_UPLOADS = 4

# ── Kanoon API (offline seed only) ────────────────────────────────────────────
KANOON_API_TOKEN = os.getenv("KANOON_API_TOKEN", "")
KANOON_API_BASE = "https://api.indiankanoon.org"
KANOON_RATE_LIMIT_DELAY = 1.0  # seconds between API calls

# ── Kanoon Seed Queries ──────────────────────────────────────────────────────
KANOON_SEED_QUERIES = [
    {
        "category": "divorce_cruelty",
        "query": '"cruelty" "divorce" "Hindu Marriage Act"',
        "doctypes": "supremecourt,highcourts",
        "max_results": 100,
    },
    {
        "category": "maintenance",
        "query": '"maintenance" "section 125" wife husband',
        "doctypes": "supremecourt,highcourts",
        "max_results": 100,
    },
    {
        "category": "child_custody",
        "query": '"child custody" "welfare of child" guardian',
        "doctypes": "supremecourt,highcourts",
        "max_results": 100,
    },
    {
        "category": "domestic_violence",
        "query": '"domestic violence" "protection" women',
        "doctypes": "supremecourt,highcourts",
        "max_results": 100,
    },
    {
        "category": "dowry_498a",
        "query": '"dowry" "498A" "harassment"',
        "doctypes": "supremecourt,highcourts",
        "max_results": 100,
    },
]

# ── Legal Query Enhancement ──────────────────────────────────────────────────
LEGAL_SYNONYMS = {
    "divorce": ["dissolution of marriage", "Section 13 HMA", "Hindu Marriage Act", "matrimonial relief"],
    "cruelty": ["mental cruelty", "physical cruelty", "Section 13(1)(ia)", "matrimonial cruelty"],
    "maintenance": ["Section 125 CrPC", "Section 24 HMA", "Section 25 HMA", "interim maintenance", "alimony", "permanent alimony"],
    "custody": ["child custody", "welfare of child", "Section 6 GWA", "Section 26 HMA", "visitation rights", "guardian"],
    "domestic violence": ["DV Act 2005", "protection order", "shared household", "Protection of Women from Domestic Violence"],
    "dowry": ["Section 498A IPC", "dowry prohibition", "dowry harassment", "cruelty by husband", "Dowry Prohibition Act"],
    "498a": ["Section 498A", "dowry harassment", "cruelty by husband or relatives"],
    "alimony": ["maintenance", "Section 25 HMA", "permanent alimony", "interim maintenance"],
}
