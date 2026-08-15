import asyncio
import argparse
import sys
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config
from app.db.models import Base, KanoonDocument, CaseType
from app.core.kanoon_client import KanoonClient
from app.core.document_processor import extract_text_from_kanoon_html, legal_aware_chunk
from app.core.embeddings import EmbeddingService
from app.core.vector_store import VectorStore


def init_sync_db():
    """Create a synchronous DB session for the seed script."""
    # Convert async SQLite URL to sync URL
    sync_url = config.DATABASE_URL.replace("sqlite+aiosqlite", "sqlite")
    engine = create_engine(sync_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


async def seed_kanoon():
    """One-time corpus builder fetching from Kanoon API."""
    print("Initializing components...")
    db_session = init_sync_db()
    client = KanoonClient()
    embedding_service = EmbeddingService()
    vector_store = VectorStore()
    
    total_docs_processed = 0
    total_chunks_added = 0
    
    seen_doc_ids = set()
    
    for seed in config.KANOON_SEED_QUERIES:
        category = seed['category']
        query = seed['query']
        doctypes = seed['doctypes']
        max_results = seed['max_results']
        
        print(f"\nProcessing category: {category} (Query: {query})")
        
        # Determine max pages (assuming 10 results per page)
        maxpages = max(1, max_results // 10)
        
        doc_ids_to_fetch = []
        
        for pagenum in range(maxpages):
            try:
                print(f"  Searching page {pagenum}...")
                search_results = await client.search(query, doctypes, pagenum=pagenum)
                
                docs = search_results.get('docs', [])
                if not docs:
                    print(f"  No more results on page {pagenum}.")
                    break
                    
                for doc in docs:
                    doc_id = str(doc.get('tid'))
                    if doc_id and doc_id not in seen_doc_ids:
                        seen_doc_ids.add(doc_id)
                        doc_ids_to_fetch.append(doc_id)
                        
                if len(doc_ids_to_fetch) >= max_results:
                    doc_ids_to_fetch = doc_ids_to_fetch[:max_results]
                    break
                    
            except Exception as e:
                print(f"  Error searching page {pagenum}: {e}")
                continue
                
        print(f"  Found {len(doc_ids_to_fetch)} unique documents to fetch.")
        
        for idx, doc_id in enumerate(doc_ids_to_fetch):
            print(f"  [{idx+1}/{len(doc_ids_to_fetch)}] Fetching doc {doc_id}...")
            
            try:
                # Check if already in DB
                existing = db_session.query(KanoonDocument).filter(KanoonDocument.kanoon_doc_id == doc_id).first()
                if existing:
                    print(f"    Already in database, skipping.")
                    continue
                    
                # Fetch full doc
                doc_data = await client.get_document(doc_id)
                content_html = doc_data.get('doc', '')
                if not content_html:
                    content_html = doc_data.get('docsource', '')
                    
                if not content_html:
                    print(f"    No content found for doc {doc_id}.")
                    continue
                    
                # Fetch metadata
                meta_data = await client.get_doc_metadata(doc_id)
                title = meta_data.get('title', f"Document {doc_id}")
                court = meta_data.get('court', '')
                date_str = meta_data.get('publishdate', '')
                
                # Extract text
                text = extract_text_from_kanoon_html(content_html)
                if not text.strip():
                    print(f"    Extracted text is empty.")
                    continue
                    
                # Build metadata dict for chunks
                chunk_metadata = {
                    "source_type": "kanoon",
                    "kanoon_doc_id": doc_id,
                    "title": title,
                    "court": court,
                    "date": date_str,
                    "category": category
                }
                
                # Chunk text
                chunks = legal_aware_chunk(text, chunk_metadata)
                
                if not chunks:
                    print(f"    No chunks generated.")
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
                    kanoon_doc_id=doc_id,
                    title=title,
                    court=court,
                    date=date_str,
                    category=CaseType(category) if category in [c.value for c in CaseType] else None,
                    chunk_count=len(chunks)
                )
                db_session.add(db_doc)
                db_session.commit()
                
                total_docs_processed += 1
                total_chunks_added += len(chunks)
                print(f"    Added {len(chunks)} chunks.")
                
            except Exception as e:
                print(f"    Error processing doc {doc_id}: {e}")
                db_session.rollback()
                continue
                
    print(f"\nSeeding complete!")
    print(f"Total documents processed: {total_docs_processed}")
    print(f"Total chunks added to vector store: {total_chunks_added}")
    
    db_session.close()

if __name__ == "__main__":
    asyncio.run(seed_kanoon())
