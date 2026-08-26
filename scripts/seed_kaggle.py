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
PAGES_TO_SCAN = 20  # Scan first 20 pages for keywords

KEYWORDS_MAP = {
    "divorce": CaseType.DIVORCE,
    "hindu marriage act": CaseType.DIVORCE,
    "special marriage act": CaseType.DIVORCE,
    "christian marriage act": CaseType.DIVORCE,
    "dissolution of muslim marriages": CaseType.DIVORCE,
    "restitution of conjugal rights": CaseType.DIVORCE,
    "judicial separation": CaseType.DIVORCE,
    "family court": CaseType.DIVORCE,
    "matrimonial": CaseType.DIVORCE,
    "cruelty": CaseType.DIVORCE,
    "maintenance": CaseType.MAINTENANCE,
    "alimony": CaseType.MAINTENANCE,
    "125 crpc": CaseType.MAINTENANCE,
    "section 125": CaseType.MAINTENANCE,
    "child custody": CaseType.CUSTODY,
    "guardian": CaseType.CUSTODY,
    "domestic violence": CaseType.DOMESTIC_VIOLENCE,
    "pwdva": CaseType.DOMESTIC_VIOLENCE,
    "dowry": CaseType.DOWRY,
    "498a": CaseType.DOWRY,
    "498-a": CaseType.DOWRY,
    "498 a": CaseType.DOWRY
}

def init_sync_db():
    sync_url = config.DATABASE_URL.replace("sqlite+aiosqlite", "sqlite")
    engine = create_engine(sync_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

async def verify_matrimonial_llm(text: str) -> bool:
    """Uses LLMProvider to verify if a text is truly a matrimonial case."""
    prompt = f"""You are a legal classification system. Determine if the following legal document excerpt involves ANY Family Law or Matrimonial dispute. 
This includes: divorce, child custody, alimony, maintenance, domestic violence, 498A cruelty, dowry death, marital property disputes, restitution of conjugal rights, or disputes between husband and wife/in-laws.
If the case involves ANY of these elements as a central or related theme, reply with exactly one word: 'YES'. 
If it is purely a corporate, tax, service, or unrelated criminal matter, reply with 'NO'. 
Do not provide any explanation.

Excerpt:
{text[:12000]}"""
    
    messages = [{"role": "user", "content": prompt}]
    
    try:
        # Hardcoding provider="ollama" because it's a local classification task, but it could be dynamic
        llm = LLMProvider(provider="ollama")
        answer = await llm.generate_async(messages)
        return "YES" in answer.strip().upper()
    except Exception as e:
        print(f"LLM Classification failed: {e}. Defaulting to keyword match.")
        return True # Fallback to keyword if LLM fails

def calculate_matrimonial_score(pdf_path: Path):
    """Scan first few pages of PDF and return a score based on unique matrimonial keywords, and the primary CaseType."""
    try:
        extracted_text = ""
        with fitz.open(pdf_path) as doc:
            for i in range(min(PAGES_TO_SCAN, len(doc))):
                extracted_text += doc[i].get_text().lower() + "\n"
                
        matched_keywords = []
        primary_case_type = None
        
        for kw, case_type in KEYWORDS_MAP.items():
            if kw in extracted_text:
                matched_keywords.append(kw)
                if not primary_case_type:
                    primary_case_type = case_type
                    
        return len(matched_keywords), primary_case_type, matched_keywords
    except Exception:
        return 0, None, []

def extract_full_text(pdf_path: Path):
    text = ""
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text() + "\n"
    except Exception as e:
        print(f"Error reading PDF {pdf_path.name}: {e}")
    return text

async def score_case(case):
    score, case_type, keywords = await asyncio.to_thread(calculate_matrimonial_score, case["pdf_path"])
    case["score"] = score
    case["case_type"] = case_type
    case["keywords"] = keywords
    return case

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
    
    # Filter out existing cases synchronously first
    new_cases = []
    for case in cases_to_process:
        pdf_filename = case["pdf_path"].name
        existing = db_session.query(KanoonDocument).filter(KanoonDocument.kanoon_doc_id == pdf_filename).first()
        if not existing:
            new_cases.append(case)
            
    print(f"{len(new_cases)} new cases require processing. Scanning all cases for keyword scoring...")
    
    # Concurrently score all cases
    tasks = [score_case(case) for case in new_cases]
    scored_results = await asyncio.gather(*tasks)
    
    # Filter cases with at least 1 keyword and sort by score descending
    valid_cases = [c for c in scored_results if c["score"] > 0]
    valid_cases.sort(key=lambda x: x["score"], reverse=True)
    
    print(f"Found {len(valid_cases)} potential matrimonial cases. Processing top {TARGET_CASES}...")
    
    for case in valid_cases[:TARGET_CASES]:
        case_type = case["case_type"]
        print(f"  [+] Processing case (Score: {case['score']}) ({case_type.value}): {case['pet']} vs {case['res']}")
        print(f"      Keywords found: {case['keywords']}")
        
        pdf_path = case["pdf_path"]
        pdf_filename = pdf_path.name
        
        # Process the case
        text = extract_full_text(pdf_path)
        if not text.strip():
            continue
            
        title = f"{case['pet'][:100]} vs {case['res'][:100]}"
        
        chunk_metadata = {
            "source_type": "kanoon", 
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
