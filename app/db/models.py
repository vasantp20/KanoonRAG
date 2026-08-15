"""
KanoonRAG — SQLAlchemy ORM Models

All database tables for multi-tenant case management.
"""

import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    Enum,
    JSON,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


# ── Enums ──────────────────────────────────────────────────────────────────────


class CaseType(str, enum.Enum):
    DIVORCE = "divorce_cruelty"
    MAINTENANCE = "maintenance"
    CUSTODY = "child_custody"
    DOMESTIC_VIOLENCE = "domestic_violence"
    DOWRY = "dowry_498a"
    OTHER = "other"


class CaseStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"


class DocType(str, enum.Enum):
    CASE_BRIEF = "case_brief"
    LEGAL_NOTICE = "legal_notice"
    CASE_ANALYSIS = "case_analysis"


# ── Models ─────────────────────────────────────────────────────────────────────


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    clients = relationship("Client", back_populates="user", cascade="all, delete-orphan")
    cases = relationship("Case", back_populates="user", cascade="all, delete-orphan")
    query_logs = relationship("QueryLog", back_populates="user", cascade="all, delete-orphan")
    generated_documents = relationship("GeneratedDocument", back_populates="user", cascade="all, delete-orphan")


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    age = Column(Integer, nullable=True)
    gender = Column(String(20), nullable=True)
    place_of_stay = Column(String(255), nullable=True)
    contact_info = Column(String(255), nullable=True)
    initial_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="clients")
    cases = relationship("Case", back_populates="client", cascade="all, delete-orphan")


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    case_type = Column(Enum(CaseType), nullable=False)
    description = Column(Text, nullable=True)
    opposing_party_name = Column(String(255), nullable=True)
    opposing_legal_rep = Column(String(255), nullable=True)
    opposing_party_address = Column(Text, nullable=True)
    court_name = Column(String(255), nullable=True)
    status = Column(Enum(CaseStatus), default=CaseStatus.DRAFT)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    client = relationship("Client", back_populates="cases")
    user = relationship("User", back_populates="cases")
    uploaded_documents = relationship("UploadedDocument", back_populates="case", cascade="all, delete-orphan")
    query_logs = relationship("QueryLog", back_populates="case", cascade="all, delete-orphan")
    generated_documents = relationship("GeneratedDocument", back_populates="case", cascade="all, delete-orphan")


class UploadedDocument(Base):
    __tablename__ = "uploaded_documents"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_type = Column(String(10), nullable=False)  # "pdf" or "docx"
    processed = Column(Boolean, default=False)
    chunk_count = Column(Integer, default=0)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    case = relationship("Case", back_populates="uploaded_documents")


class KanoonDocument(Base):
    __tablename__ = "kanoon_documents"

    id = Column(Integer, primary_key=True, index=True)
    kanoon_doc_id = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(Text, nullable=False)
    court = Column(String(255), nullable=True)
    date = Column(String(50), nullable=True)
    citation = Column(String(255), nullable=True)
    judges = Column(Text, nullable=True)
    category = Column(Enum(CaseType), nullable=True)
    chunk_count = Column(Integer, default=0)
    fetched_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class QueryLog(Base):
    __tablename__ = "query_logs"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), index=True, nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    query_text = Column(Text, nullable=False)
    response_text = Column(Text, nullable=True)
    sources_used = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    case = relationship("Case", back_populates="query_logs")
    user = relationship("User", back_populates="query_logs")


class GeneratedDocument(Base):
    __tablename__ = "generated_documents"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    doc_type = Column(Enum(DocType), nullable=False)
    file_path = Column(String(512), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    case = relationship("Case", back_populates="generated_documents")
    user = relationship("User", back_populates="generated_documents")
