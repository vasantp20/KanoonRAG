import asyncio
import os
import sys
import pandas as pd
from pathlib import Path
import fitz  # PyMuPDF
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config
from app.db.models import Base, KanoonDocument, CaseType
from app.core.document_processor import legal_aware_chunk
from app.core.embeddings import EmbeddingService
from app.core.vector_store import VectorStore

KAGGLE_DIR = Path("data/kaggle")
PDF_DIR = KAGGLE_DIR / "pdfs"
GOLDEN_DATASET_PATH = Path("tests/golden_dataset_ragas.csv")

def init_sync_db():
    sync_url = config.DATABASE_URL.replace("sqlite+aiosqlite", "sqlite")
    engine = create_engine(sync_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

def extract_full_text(pdf_path: Path):
    text = ""
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text() + "\n"
    except Exception as e:
        print(f"Error reading PDF {pdf_path.name}: {e}")
    return text

async def seed_golden():
    print("Initializing components...")
    db_session = init_sync_db()
    embedding_service = EmbeddingService()
    vector_store = VectorStore()
    
    if not GOLDEN_DATASET_PATH.exists():
        print(f"Error: Golden dataset not found at {GOLDEN_DATASET_PATH}")
        return
        
    df = pd.read_csv(GOLDEN_DATASET_PATH)
    # We only process the top 5 to match our evaluation loop
    df = df.head(5)
    
    pdf_filenames = df['source_pdf'].dropna().unique().tolist()
    print(f"Found {len(pdf_filenames)} unique source PDFs for the golden evaluation subset.")
    
    processed_count = 0
    total_chunks_added = 0
    
    for idx, pdf_filename in enumerate(pdf_filenames):
        pdf_path = PDF_DIR / pdf_filename
        
        if not pdf_path.exists():
            print(f"  [{idx}] WARNING: PDF {pdf_filename} not found in {PDF_DIR}! Skipping.")
            continue
            
        existing = db_session.query(KanoonDocument).filter(KanoonDocument.kanoon_doc_id == pdf_filename).first()
        if existing:
            print(f"  [{idx}] Skipping {pdf_filename} (already in DB)")
            continue
            
        print(f"  [{idx}] Processing golden case: {pdf_filename}")
        text = extract_full_text(pdf_path)
        if not text.strip():
            print(f"    Empty text, skipping.")
            continue
            
        chunk_metadata = {
            "source_type": "kanoon",
            "kanoon_doc_id": pdf_filename,
            "title": f"Golden Eval Case {idx+1}",
            "court": "Supreme Court of India",
            "date": "Unknown",
        }
        
        chunks = legal_aware_chunk(text, chunk_metadata)
        if not chunks:
            continue
            
        texts_to_embed = [c['text'] for c in chunks]
        embeddings = embedding_service.embed_documents(texts_to_embed)
        
        for chunk, emb in zip(chunks, embeddings):
            chunk['embedding'] = emb
            
        vector_store.add_kanoon_chunks(chunks)
        
        db_doc = KanoonDocument(
            kanoon_doc_id=pdf_filename,
            title=f"Golden Eval Case {idx+1}",
            court="Supreme Court of India",
            date="Unknown",
            chunk_count=len(chunks)
        )
        db_session.add(db_doc)
        db_session.commit()
        
        processed_count += 1
        total_chunks_added += len(chunks)
        print(f"    Added {len(chunks)} chunks.")
        
    print(f"\nGolden Seeding complete!")
    print(f"Total documents processed: {processed_count}")
    print(f"Total chunks added: {total_chunks_added}")
    db_session.close()

if __name__ == "__main__":
    asyncio.run(seed_golden())
