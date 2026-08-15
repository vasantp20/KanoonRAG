"""
KanoonRAG — Kanoon Browse Endpoint

Browse the pre-fetched case law corpus stored in SQLite.
No Kanoon API calls — reads directly from the KanoonDocument table.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pathlib import Path

from app.db.database import get_db
from app.db.models import KanoonDocument, User
from app.api.schemas import KanoonDocumentResponse
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/kanoon", tags=["kanoon"])


@router.get("/browse", response_model=List[KanoonDocumentResponse])
async def browse_kanoon(
    category: Optional[str] = Query(None, description="Filter by case category"),
    court: Optional[str] = Query(None, description="Filter by court name (substring match)"),
    search: Optional[str] = Query(None, description="Search in case titles"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Browse the pre-fetched Kanoon case law corpus.

    Supports filtering by category, court, and title search.
    Returns paginated results from the SQLite KanoonDocument table.
    """
    query = select(KanoonDocument)

    if category:
        query = query.where(KanoonDocument.category == category)

    if court:
        query = query.where(KanoonDocument.court.ilike(f"%{court}%"))

    if search:
        query = query.where(KanoonDocument.title.ilike(f"%{search}%"))

    query = query.order_by(KanoonDocument.fetched_at.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    docs = result.scalars().all()

    return docs


@router.get("/stats")
async def kanoon_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return corpus statistics."""
    from sqlalchemy import func

    total = await db.execute(select(func.count(KanoonDocument.id)))
    total_count = total.scalar() or 0

    total_chunks = await db.execute(select(func.sum(KanoonDocument.chunk_count)))
    chunk_count = total_chunks.scalar() or 0

    return {
        "total_documents": total_count,
        "total_chunks": chunk_count,
    }

@router.get("/download/{doc_id}")
async def download_kanoon_doc(
    doc_id: str,
    current_user: User = Depends(get_current_user),
):
    """Serve the local PDF file from the Kaggle dataset."""
    pdf_path = Path("data/kaggle/pdfs") / doc_id
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="Document not found locally")
        
    return FileResponse(
        path=pdf_path,
        filename=doc_id,
        media_type="application/pdf"
    )
