"""
KanoonRAG — Document Generation Endpoints

Generates DOCX legal documents (case briefs, legal notices, case analysis memos)
using RAGEngine for content and DocumentGenerator for formatting.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.database import get_db
from app.db.models import GeneratedDocument, Case, Client, User, DocType
from app.api.schemas import DocumentGenerateRequest, DocumentGenerateResponse
from app.api.dependencies import get_current_user
from app.core.document_generator import DocumentGenerator
from app.core.rag_engine import RAGEngine
from app.core.vector_store import VectorStore
from app.core.embeddings import EmbeddingService

router = APIRouter(prefix="/documents", tags=["documents"])

rag_engine = RAGEngine()
doc_gen = DocumentGenerator()
embedding_service = EmbeddingService()
vector_store = VectorStore()

# Section definitions for each document type
SECTION_DEFS = {
    DocType.CASE_BRIEF: [
        ("facts", "Material Facts"),
        ("issues", "Issues Presented"),
        ("applicable_law", "Applicable Law"),
        ("precedent_analysis", "Analysis of Precedents"),
        ("arguments", "Arguments"),
        ("prayer", "Conclusion / Prayer"),
    ],
    DocType.LEGAL_NOTICE: [
        ("introduction", "Introduction"),
        ("facts", "Facts and Background"),
        ("breach", "Grievance / Breach"),
        ("demands", "Demands"),
        ("consequences", "Consequences of Non-Compliance"),
    ],
    DocType.CASE_ANALYSIS: [
        ("summary", "Executive Summary"),
        ("strengths", "Strengths of the Case"),
        ("weaknesses", "Weaknesses and Risks"),
        ("strategy", "Proposed Strategy"),
    ],
}


@router.post("/generate", response_model=DocumentGenerateResponse)
async def generate_document(
    request: DocumentGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a legal document (DOCX) for a given case.

    Uses RAGEngine to generate content for each section, then
    DocumentGenerator to assemble the DOCX with professional formatting.
    """
    # Fetch case and client
    result = await db.execute(
        select(Case).where(Case.id == request.case_id, Case.user_id == current_user.id)
    )
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    client_res = await db.execute(select(Client).where(Client.id == case.client_id))
    client = client_res.scalar_one_or_none()

    case_info = {
        "user_id": current_user.id,
        "case_type": case.case_type.value if case.case_type else "unknown",
        "client_name": client.name if client else "Unknown",
        "client_age": client.age if client else None,
        "client_gender": client.gender if client else None,
        "client_place_of_stay": client.place_of_stay if client else None,
        "opposing_party_name": case.opposing_party_name or "N/A",
        "court_name": case.court_name or "N/A",
        "description": case.description or "",
    }

    # Retrieve relevant context once for all sections
    search_query = f"{case.case_type.value} {case.description or ''} {case.opposing_party_name or ''}"
    query_embedding = embedding_service.embed_query(search_query)
    context_chunks = vector_store.search_all(query_embedding, current_user.id, case.id)

    # Generate content for each section
    section_defs = SECTION_DEFS.get(request.doc_type, [])
    sections = {}

    for section_key, section_name in section_defs:
        try:
            content = await rag_engine.generate_document_section(
                section_name=section_name,
                case_info=case_info,
                context_chunks=context_chunks,
            )
            sections[section_key] = content
        except Exception as e:
            sections[section_key] = f"[Error generating section: {str(e)}]"

    # Build references from context chunks
    references = []
    seen_ids = set()
    for chunk in context_chunks:
        meta = chunk.get("metadata", {})
        doc_id = meta.get("kanoon_doc_id")
        if doc_id and doc_id not in seen_ids:
            seen_ids.add(doc_id)
            references.append({
                "title": meta.get("title", "Unknown Case"),
                "court": meta.get("court"),
                "date": meta.get("date"),
                "kanoon_doc_id": doc_id,
                "snippet": chunk["text"][:200],
            })

    # Create DOCX
    try:
        if request.doc_type == DocType.CASE_BRIEF:
            file_path = doc_gen.generate_case_brief(case_info, sections, references)
        elif request.doc_type == DocType.LEGAL_NOTICE:
            file_path = doc_gen.generate_legal_notice(case_info, sections, references)
        elif request.doc_type == DocType.CASE_ANALYSIS:
            file_path = doc_gen.generate_case_analysis(case_info, sections, references)
        else:
            raise HTTPException(status_code=400, detail="Invalid doc_type")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document generation failed: {str(e)}")

    # Save record
    gen_doc = GeneratedDocument(
        user_id=current_user.id,
        case_id=case.id,
        doc_type=request.doc_type,
        file_path=file_path,
    )
    db.add(gen_doc)
    await db.commit()
    await db.refresh(gen_doc)

    return gen_doc


@router.get("/{doc_id}/download")
async def download_document(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download a generated DOCX document."""
    result = await db.execute(
        select(GeneratedDocument).where(
            GeneratedDocument.id == doc_id,
            GeneratedDocument.user_id == current_user.id,
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return FileResponse(
        path=doc.file_path,
        filename=doc.file_path.split("/")[-1],
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@router.get("/", response_model=List[DocumentGenerateResponse])
async def list_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all generated documents for the current user."""
    result = await db.execute(
        select(GeneratedDocument).where(GeneratedDocument.user_id == current_user.id)
    )
    return result.scalars().all()
