"""
KanoonRAG — Pydantic Schemas

Request/response models for all API endpoints.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.db.models import CaseType, CaseStatus, DocType


# ── Auth ───────────────────────────────────────────────────────────────────────


class UserRegister(BaseModel):
    email: str = Field(..., min_length=5)
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=1)


class UserLogin(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── Client ─────────────────────────────────────────────────────────────────────


class ClientCreate(BaseModel):
    name: str = Field(..., min_length=1)
    age: Optional[int] = Field(None, ge=0, le=150)
    gender: Optional[str] = None
    place_of_stay: Optional[str] = None
    contact_info: Optional[str] = None
    initial_notes: Optional[str] = None


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = Field(None, ge=0, le=150)
    gender: Optional[str] = None
    place_of_stay: Optional[str] = None
    contact_info: Optional[str] = None
    initial_notes: Optional[str] = None


class ClientResponse(BaseModel):
    id: int
    name: str
    age: Optional[int]
    gender: Optional[str]
    place_of_stay: Optional[str]
    contact_info: Optional[str]
    initial_notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ── Case ───────────────────────────────────────────────────────────────────────


class CaseCreate(BaseModel):
    client_id: int
    case_type: CaseType
    description: Optional[str] = None
    opposing_party_name: Optional[str] = None
    opposing_legal_rep: Optional[str] = None
    opposing_party_address: Optional[str] = None
    court_name: Optional[str] = None


class CaseUpdate(BaseModel):
    case_type: Optional[CaseType] = None
    description: Optional[str] = None
    opposing_party_name: Optional[str] = None
    opposing_legal_rep: Optional[str] = None
    opposing_party_address: Optional[str] = None
    court_name: Optional[str] = None
    status: Optional[CaseStatus] = None


class CaseResponse(BaseModel):
    id: int
    client_id: int
    case_type: CaseType
    description: Optional[str]
    opposing_party_name: Optional[str]
    opposing_legal_rep: Optional[str]
    opposing_party_address: Optional[str]
    court_name: Optional[str]
    status: CaseStatus
    created_at: datetime

    class Config:
        from_attributes = True


# ── Uploaded Document ─────────────────────────────────────────────────────────


class UploadedDocumentResponse(BaseModel):
    id: int
    case_id: int
    filename: str
    file_type: str
    processed: bool
    chunk_count: int
    uploaded_at: datetime

    class Config:
        from_attributes = True


# ── Query ──────────────────────────────────────────────────────────────────────


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1)
    case_id: Optional[int] = None
    session_id: Optional[str] = None


class SourceReference(BaseModel):
    source_type: str  # "kanoon" or "upload"
    title: str
    citation: Optional[str] = None
    court: Optional[str] = None
    date: Optional[str] = None
    kanoon_doc_id: Optional[str] = None
    filename: Optional[str] = None
    page_num: Optional[int] = None
    relevance_score: float
    snippet: str
    full_text: Optional[str] = None


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceReference]
    query_id: int
    session_id: str

class SessionSummaryResponse(BaseModel):
    session_id: str
    title: str
    desc: str
    time: str
    created_at: datetime

class SessionHistoryItem(BaseModel):
    id: int
    query_text: str
    response_text: Optional[str]
    sources_used: Optional[list] = None
    created_at: datetime


# ── Document Generation ──────────────────────────────────────────────────────


class DocumentGenerateRequest(BaseModel):
    case_id: int
    doc_type: DocType
    additional_instructions: Optional[str] = None


class DocumentGenerateResponse(BaseModel):
    id: int
    doc_type: DocType
    file_path: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── Kanoon Browse ────────────────────────────────────────────────────────────


class KanoonDocumentResponse(BaseModel):
    id: int
    kanoon_doc_id: str
    title: str
    court: Optional[str]
    date: Optional[str]
    citation: Optional[str]
    judges: Optional[str]
    category: Optional[CaseType]
    chunk_count: int = 0

    class Config:
        from_attributes = True
