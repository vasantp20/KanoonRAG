import asyncio
import os
import sys
import csv
from pathlib import Path
import fitz  # PyMuPDF
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config
from app.db.models import Base, KanoonDocument, CaseType
from app.core.document_processor import legal_aware_chunk
from app.core.embeddings import EmbeddingService
from app.core.vector_store import VectorStore

KAGGLE_DIR = Path("data/kaggle")
CSV_PATH = KAGGLE_DIR / "judgments.csv"
PDF_DIR = KAGGLE_DIR / "pdfs"

TARGET_CASES = 500
PAGES_TO_SCAN = 3  # Scan first 3 pages for keywords

KEYWORDS_MAP = {
    "divorce": CaseType.DIVORCE,
    "hindu marriage act": CaseType.DIVORCE,
    "special marriage act": CaseType.DIVORCE,
    "cruelty": CaseType.DIVORCE,
    "maintenance": CaseType.MAINTENANCE,
    "alimony": CaseType.MAINTENANCE,
    "125 crpc": CaseType.MAINTENANCE,
    "child custody": CaseType.CUSTODY,
    "guardian": CaseType.CUSTODY,
    "domestic violence": CaseType.DOMESTIC_VIOLENCE,
    "pwdva": CaseType.DOMESTIC_VIOLENCE,
    "dowry": CaseType.DOWRY,
    "498a": CaseType.DOWRY
}

def init_sync_db():
    sync_url = config.DATABASE_URL.replace("sqlite+aiosqlite", "sqlite")
    engine = create_engine(sync_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

def check_matrimonial(pdf_path: Path):
    """Scan first few pages of PDF for matrimonial keywords. Returns matched CaseType or None."""
    try:
        with fitz.open(pdf_path) as doc:
            for i in range(min(PAGES_TO_SCAN, len(doc))):
                text = doc[i].get_text().lower()
                for kw, case_type in KEYWORDS_MAP.items():
                    if kw in text:
                        return case_type
    except Exception:
        pass
    return None

def extract_full_text(pdf_path: Path):
    text = ""
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text() + "\n"
    except Exception as e:
        print(f"Error reading PDF {pdf_path.name}: {e}")
    return text

async def seed_kaggle():
    print("Initializing components...")
    db_session = init_sync_db()
    embedding_service = EmbeddingService()
    vector_store = VectorStore()
    
    if not CSV_PATH.exists() or not PDF_DIR.exists():
        print(f"Error: Dataset not found in {KAGGLE_DIR}")
        return
        
    print(f"Reading {CSV_PATH}...")
    cases_to_process = []
    
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            diary_no = row.get("diary_no", "")
            temp_link = row.get("temp_link", "")
            if not temp_link:
                continue
            
            # Reconstruct the PDF filename as stored in Kaggle dataset
            safe_link = temp_link.replace("/", "__")
            pdf_filename = f"{diary_no}___{safe_link}"
            pdf_path = PDF_DIR / pdf_filename
            
            if pdf_path.exists():
                cases_to_process.append({
                    "diary_no": diary_no,
                    "pdf_path": pdf_path,
                    "pet": row.get("pet", "Unknown Petitioner"),
                    "res": row.get("res", "Unknown Respondent"),
                    "date": row.get("judgment_dates", "Unknown Date"),
                    "court": "Supreme Court of India",
                    "citation": row.get("case_no", "")
                })

    print(f"Found {len(cases_to_process)} matching PDFs. Scanning for matrimonial cases...")
    
    processed_count = 0
    total_chunks_added = 0
    
    for idx, case in enumerate(cases_to_process):
        if processed_count >= TARGET_CASES:
            break
            
        pdf_path = case["pdf_path"]
        pdf_filename = pdf_path.name
        
        # Check if already processed
        existing = db_session.query(KanoonDocument).filter(KanoonDocument.kanoon_doc_id == pdf_filename).first()
        if existing:
            print(f"  [{idx}] Skipping {pdf_filename} (already in DB)")
            continue
            
        # Fast filter
        case_type = check_matrimonial(pdf_path)
        if not case_type:
            continue
            
        print(f"  [{idx}] Found matrimonial case! ({case_type.value}): {case['pet']} vs {case['res']}")
        
        # Process the case
        text = extract_full_text(pdf_path)
        if not text.strip():
            continue
            
        title = f"{case['pet'][:100]} vs {case['res'][:100]}"
        
        chunk_metadata = {
            "source_type": "kanoon", # Keeping 'kanoon' as source_type to avoid changing frontend filters
            "kanoon_doc_id": pdf_filename,
            "title": title,
            "court": case["court"],
            "date": case["date"],
            "category": case_type.value
        }
        
        chunks = legal_aware_chunk(text, chunk_metadata)
        if not chunks:
            continue
            
        # Generate embeddings
        texts_to_embed = [c['text'] for c in chunks]
        embeddings = embedding_service.embed_documents(texts_to_embed)
        
        for chunk, emb in zip(chunks, embeddings):
            chunk['embedding'] = emb
            
        # Store in VectorStore
        vector_store.add_kanoon_chunks(chunks)
        
        # Store in SQLite
        db_doc = KanoonDocument(
            kanoon_doc_id=pdf_filename,
            title=title,
            court=case["court"],
            date=case["date"],
            citation=case["citation"],
            category=case_type,
            chunk_count=len(chunks)
        )
        db_session.add(db_doc)
        db_session.commit()
        
        processed_count += 1
        total_chunks_added += len(chunks)
        print(f"    Added {len(chunks)} chunks. Total processed: {processed_count}/{TARGET_CASES}")
        
    print(f"\nSeeding complete!")
    print(f"Total documents processed: {processed_count}")
    print(f"Total chunks added to vector store: {total_chunks_added}")
    
    db_session.close()

if __name__ == "__main__":
    asyncio.run(seed_kaggle())
