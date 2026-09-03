"""
KanoonRAG — RAG Query Endpoint

Handles natural language queries against the pre-built case law corpus and
uploaded client documents. Uses the real RAGEngine and proper auth.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from sqlalchemy.future import select
from sqlalchemy import func, and_
from typing import List, Dict
from datetime import datetime, timezone

from app.db.database import get_db
from app.db.models import QueryLog, Case, Client, User
from app.api.schemas import QueryRequest, QueryResponse, SourceReference, SessionSummaryResponse, SessionHistoryItem
from app.api.dependencies import get_current_user, get_rag_engine
from app.core.rag_engine.engine import RAGEngine

router = APIRouter(prefix="/query", tags=["query"])

async def _get_chat_history(session_id: str, case_id: int, user_id: int, db: AsyncSession) -> List[Dict[str, str]]:
    chat_history = []
    where_clauses = [QueryLog.user_id == user_id]
    
    if session_id:
        where_clauses.append(QueryLog.session_id == session_id)
    elif case_id:
        where_clauses.append(QueryLog.case_id == case_id)
    else:
        return []
        
    history_result = await db.execute(
        select(QueryLog).where(*where_clauses).order_by(QueryLog.created_at.desc()).limit(5)
    )
    logs = history_result.scalars().all()
    logs.reverse()
    for log in logs:
        if log.query_text and log.response_text:
            chat_history.append({
                "query": log.query_text,
                "response": log.response_text
            })
    return chat_history


@router.post("/", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    rag_engine: RAGEngine = Depends(get_rag_engine),
):
    """
    Process a legal RAG query.

    Optionally scoped to a specific case to include client info and
    uploaded documents in the retrieval context.
    """
    client_info = None

    if request.case_id:
        # Fetch case and client info for context
        result = await db.execute(
            select(Case).where(Case.id == request.case_id, Case.user_id == current_user.id)
        )
        case = result.scalar_one_or_none()
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        client_res = await db.execute(select(Client).where(Client.id == case.client_id))
        client = client_res.scalar_one_or_none()

        if client:
            client_info = {
                "name": client.name,
                "age": client.age,
                "gender": client.gender,
                "place_of_stay": client.place_of_stay,
                "case_type": case.case_type.value if case.case_type else None,
                "description": case.description,
                "opposing_party_name": case.opposing_party_name,
                "court_name": case.court_name,
            }

    session_id = request.session_id
    chat_history = await _get_chat_history(session_id, request.case_id, current_user.id, db)

    if not session_id:
        session_id = str(uuid.uuid4())

    # Call the real RAG engine
    try:
        rag_result = await rag_engine.query(
            user_query=request.query,
            user_id=current_user.id,
            case_id=request.case_id,
            client_info=client_info,
            chat_history=chat_history,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG query failed: {str(e)}")

    # Build typed source references
    sources = []
    for src in rag_result.get("sources", []):
        sources.append(
            SourceReference(
                source_type=src.get("source_type", "unknown"),
                title=src.get("title", "Unknown"),
                citation=src.get("citation"),
                court=src.get("court"),
                date=src.get("date"),
                kanoon_doc_id=src.get("kanoon_doc_id"),
                filename=src.get("filename"),
                page_num=src.get("page_num"),
                relevance_score=src.get("relevance_score", 0.0),
                snippet=src.get("snippet", ""),
                full_text=src.get("full_text"),
            )
        )

    # Save query log
    query_log = QueryLog(
        session_id=session_id,
        user_id=current_user.id,
        case_id=request.case_id,
        query_text=request.query,
        response_text=rag_result["answer"],
        sources_used=[s.model_dump() for s in sources],
    )
    db.add(query_log)
    await db.commit()
    await db.refresh(query_log)

    return QueryResponse(
        answer=rag_result["answer"],
        sources=sources,
        query_id=query_log.id,
        session_id=session_id,
    )

@router.get("/sessions", response_model=List[SessionSummaryResponse])
async def get_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all general research sessions for the user."""
    subq = select(
        QueryLog.session_id,
        func.min(QueryLog.created_at).label("min_created_at")
    ).where(
        QueryLog.user_id == current_user.id,
        QueryLog.case_id == None,
        QueryLog.session_id != None
    ).group_by(QueryLog.session_id).subquery()
    
    q = select(QueryLog).join(
        subq,
        and_(
            QueryLog.session_id == subq.c.session_id,
            QueryLog.created_at == subq.c.min_created_at
        )
    ).order_by(QueryLog.created_at.desc())
    
    result = await db.execute(q)
    logs = result.scalars().all()
    
    sessions = []
    for log in logs:
        now = datetime.now(timezone.utc)
        
        # log.created_at may be naive, if so add utcinfo
        created_at = log.created_at.replace(tzinfo=timezone.utc) if log.created_at.tzinfo is None else log.created_at
        diff = now - created_at
        
        if diff.days > 0:
            time_str = f"{diff.days}d ago"
        elif diff.seconds >= 3600:
            time_str = f"{diff.seconds // 3600}h ago"
        elif diff.seconds >= 60:
            time_str = f"{diff.seconds // 60}m ago"
        else:
            time_str = "Just now"
            
        sessions.append(
            SessionSummaryResponse(
                session_id=log.session_id,
                title=log.query_text[:50] + ("..." if len(log.query_text) > 50 else ""),
                desc=log.response_text[:80] + ("..." if log.response_text and len(log.response_text) > 80 else "") if log.response_text else "",
                time=time_str,
                created_at=created_at
            )
        )
        
    return sessions


@router.get("/sessions/{session_id}", response_model=List[SessionHistoryItem])
async def get_session_history(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all queries and responses for a specific session."""
    q = select(QueryLog).where(
        QueryLog.session_id == session_id,
        QueryLog.user_id == current_user.id
    ).order_by(QueryLog.created_at.asc())
    
    result = await db.execute(q)
    logs = result.scalars().all()
    
    return [
        SessionHistoryItem(
            id=log.id,
            query_text=log.query_text,
            response_text=log.response_text,
            sources_used=log.sources_used,
            created_at=log.created_at
        )
        for log in logs
    ]

@router.get("/cases/{case_id}/history", response_model=List[SessionHistoryItem])
async def get_case_history(
    case_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all queries and responses for a specific case."""
    q = select(QueryLog).where(
        QueryLog.case_id == case_id,
        QueryLog.user_id == current_user.id
    ).order_by(QueryLog.created_at.asc())
    
    result = await db.execute(q)
    logs = result.scalars().all()
    
    return [
        SessionHistoryItem(
            id=log.id,
            query_text=log.query_text,
            response_text=log.response_text,
            sources_used=log.sources_used,
            created_at=log.created_at
        )
        for log in logs
    ]
