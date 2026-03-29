from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class DocumentIngestRequest(BaseModel):
    paths: list[str] = Field(default_factory=list)
    metadata: dict[str, dict[str, Any]] = Field(default_factory=dict)


class DocumentAuditRequest(BaseModel):
    document_id: str | None = None
    path: str | None = None


class SPCAnalyzeRequest(BaseModel):
    parameter_name: str = "SPC Parameter"
    values: list[float] = Field(default_factory=list)
    csv_text: str = ""
    lsl: float | None = None
    usl: float | None = None
    target: float | None = None


class DeviationDraftRequest(BaseModel):
    issue_description: str
    process_step: str = ""
    lot_no: str = ""
    severity: str = "medium"
    related_documents: list[str] = Field(default_factory=list)


class KnowledgeQARequest(BaseModel):
    question: str
    limit: int = Field(default=5, ge=1, le=10)
    document_id: str | None = None
    path: str | None = None


class DocumentCompareRequest(BaseModel):
    left_document_id: str | None = None
    left_path: str | None = None
    right_document_id: str | None = None
    right_path: str | None = None
    use_llm: bool = False


class DocumentVersionCandidatesRequest(BaseModel):
    document_id: str | None = None
    path: str | None = None
    limit: int = Field(default=10, ge=1, le=20)


class SendEmailRequest(BaseModel):
    to: str                  # 收件人（多位以逗號分隔）
    subject: str             # 主旨
    body: str                # 內文（純文字或 HTML）
    is_html: bool = False    # True = 寄送 HTML 格式
