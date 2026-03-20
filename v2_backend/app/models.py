from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    source_path: Mapped[str] = mapped_column(Text, unique=True, index=True)
    title: Mapped[str] = mapped_column(Text)
    document_code: Mapped[str] = mapped_column(Text, default="")
    file_type: Mapped[str] = mapped_column(Text, default="")
    version: Mapped[str] = mapped_column(Text, default="")
    owner_dept: Mapped[str] = mapped_column(Text, default="")
    source_system: Mapped[str] = mapped_column(Text, default="local")
    status: Mapped[str] = mapped_column(Text, default="active")
    full_text: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    chunks: Mapped[list["DocumentChunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    page_no: Mapped[int | None] = mapped_column(Integer, nullable=True)
    section_name: Mapped[str] = mapped_column(Text, default="")
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    document: Mapped[Document] = relationship(back_populates="chunks")

    __table_args__ = (UniqueConstraint("document_id", "chunk_index", name="uq_document_chunk_index"),)


class PromptTemplate(Base):
    __tablename__ = "prompt_templates"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    template_code: Mapped[str] = mapped_column(Text, unique=True, index=True)
    template_name: Mapped[str] = mapped_column(Text)
    task_type: Mapped[str] = mapped_column(Text, index=True)
    status: Mapped[str] = mapped_column(Text, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    versions: Mapped[list["PromptTemplateVersion"]] = relationship(back_populates="template", cascade="all, delete-orphan")


class PromptTemplateVersion(Base):
    __tablename__ = "prompt_template_versions"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    template_id: Mapped[str] = mapped_column(ForeignKey("prompt_templates.id", ondelete="CASCADE"), index=True)
    version: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default="released")
    system_prompt: Mapped[str] = mapped_column(Text)
    policy_prompt: Mapped[str] = mapped_column(Text, default="")
    user_prompt_template: Mapped[str] = mapped_column(Text)
    output_schema: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    released_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    template: Mapped[PromptTemplate] = relationship(back_populates="versions")
    release_logs: Mapped[list["PromptTemplateReleaseLog"]] = relationship(back_populates="version_ref", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("template_id", "version", name="uq_prompt_template_version"),)


class PromptTemplateReleaseLog(Base):
    __tablename__ = "prompt_template_release_logs"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    version_id: Mapped[str] = mapped_column(ForeignKey("prompt_template_versions.id", ondelete="CASCADE"), index=True)
    action: Mapped[str] = mapped_column(Text)
    note: Mapped[str] = mapped_column(Text, default="")
    actor: Mapped[str] = mapped_column(Text, default="system")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    version_ref: Mapped[PromptTemplateVersion] = relationship(back_populates="release_logs")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    trace_id: Mapped[str] = mapped_column(Text, index=True)
    task_type: Mapped[str] = mapped_column(Text, index=True)
    user_id: Mapped[str] = mapped_column(Text, default="anonymous")
    prompt_version: Mapped[str] = mapped_column(Text, default="")
    result_status: Mapped[str] = mapped_column(Text, default="success")
    request_summary: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class CompareCache(Base):
    __tablename__ = "compare_cache"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    cache_key: Mapped[str] = mapped_column(Text, unique=True, index=True)
    left_document_id: Mapped[str] = mapped_column(Text, index=True, default="")
    right_document_id: Mapped[str] = mapped_column(Text, index=True, default="")
    use_llm: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    response_json: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AuditCache(Base):
    __tablename__ = "audit_cache"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    cache_key: Mapped[str] = mapped_column(Text, unique=True, index=True)
    document_id: Mapped[str] = mapped_column(Text, index=True, default="")
    llm_enabled: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    response_json: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
