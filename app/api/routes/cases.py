import os
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.database import get_db
from app.db.models import User, Client, Case, UploadedDocument
from app.api.schemas import CaseCreate, CaseUpdate, CaseResponse, UploadedDocumentResponse
from app.api.dependencies import get_current_user
from config import UPLOAD_DIR

router = APIRouter(prefix="/cases", tags=["cases"])

@router.post("/", response_model=CaseResponse)
async def create_case(case_data: CaseCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Create a new case for a client."""
    # Verify client
    result = await db.execute(select(Client).where(Client.id == case_data.client_id, Client.user_id == current_user.id))
    if not result.scalars().first():
        raise HTTPException(status_code=404, detail="Client not found")
        
    case = Case(
        client_id=case_data.client_id,
        user_id=current_user.id,
        case_type=case_data.case_type,
        description=case_data.description,
        opposing_party_name=case_data.opposing_party_name,
        court_name=case_data.court_name
    )
    db.add(case)
    await db.commit()
    await db.refresh(case)
    return case

@router.get("/", response_model=list[CaseResponse])
async def list_cases(client_id: Optional[int] = None, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """List all cases belonging to the current user."""
    query = select(Case).where(Case.user_id == current_user.id)
    if client_id:
        query = query.where(Case.client_id == client_id)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(case_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get a specific case by ID."""
    result = await db.execute(select(Case).where(Case.id == case_id, Case.user_id == current_user.id))
    case = result.scalars().first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case

@router.put("/{case_id}", response_model=CaseResponse)
async def update_case(case_id: int, case_data: CaseUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Update a specific case."""
    result = await db.execute(select(Case).where(Case.id == case_id, Case.user_id == current_user.id))
    case = result.scalars().first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    for key, value in case_data.model_dump(exclude_unset=True).items():
        setattr(case, key, value)
        
    await db.commit()
    await db.refresh(case)
    return case

@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_case(case_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Delete a specific case."""
    result = await db.execute(select(Case).where(Case.id == case_id, Case.user_id == current_user.id))
    case = result.scalars().first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    await db.delete(case)
    await db.commit()

@router.post("/{case_id}/upload", response_model=UploadedDocumentResponse)
async def upload_document(case_id: int, file: UploadFile = File(...), db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Upload and process a document for a specific case."""
    result = await db.execute(select(Case).where(Case.id == case_id, Case.user_id == current_user.id))
    if not result.scalars().first():
        raise HTTPException(status_code=404, detail="Case not found")
        
    file_ext = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
    if file_ext not in ['pdf', 'docx']:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are allowed")
        
    upload_path = Path(UPLOAD_DIR) / str(current_user.id) / str(case_id)
    upload_path.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_path / file.filename
    with open(file_path, "wb") as f:
        f.write(await file.read())
        
    doc = UploadedDocument(
        case_id=case_id,
        user_id=current_user.id,
        filename=file.filename,
        file_path=str(file_path),
        file_type=file_ext
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    # Process the uploaded file: chunk + embed + store in vector store
    try:
        from app.core.document_processor import process_uploaded_file
        from app.core.embeddings import EmbeddingService
        from app.core.vector_store import VectorStore

        metadata = {
            "source_type": "upload",
            "user_id": current_user.id,
            "case_id": case_id,
            "file_id": doc.id,
            "filename": file.filename,
        }
        chunks = process_uploaded_file(str(file_path), metadata)

        if chunks:
            embedding_service = EmbeddingService()
            texts = [c["text"] for c in chunks]
            embeddings = embedding_service.embed_documents(texts)
            for chunk, emb in zip(chunks, embeddings):
                chunk["embedding"] = emb

            vector_store = VectorStore()
            vector_store.add_upload_chunks(chunks)

            doc.processed = True
            doc.chunk_count = len(chunks)
            await db.commit()
            await db.refresh(doc)
    except Exception as e:
        # Log error but don't fail the upload
        import logging
        logging.error(f"Error processing uploaded file: {e}")

    return doc

@router.get("/{case_id}/documents", response_model=list[UploadedDocumentResponse])
async def list_documents(case_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """List all documents for a specific case."""
    result = await db.execute(select(Case).where(Case.id == case_id, Case.user_id == current_user.id))
    if not result.scalars().first():
        raise HTTPException(status_code=404, detail="Case not found")
        
    result = await db.execute(select(UploadedDocument).where(UploadedDocument.case_id == case_id, UploadedDocument.user_id == current_user.id))
    return result.scalars().all()
