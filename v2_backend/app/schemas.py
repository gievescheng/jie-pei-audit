from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


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


# ── ERP bridge response schemas ───────────────────────────────────────────────


class AuditLogResponse(BaseModel):
    """AuditLog record enriched with resolved ERP User info."""
    id: str
    trace_id: str
    task_type: str
    user_id: str
    prompt_version: str
    result_status: str
    request_summary: str
    created_at: datetime
    auditor_id: str | None = None
    auditor_info: dict | None = Field(
        default=None,
        description="Resolved User entity from erp_qms_core (populated at read time)",
    )

    model_config = ConfigDict(from_attributes=True)


class DocumentResponse(BaseModel):
    """Document record enriched with resolved ERP Department info."""
    id: str
    source_path: str
    title: str
    document_code: str
    file_type: str
    version: str
    owner_dept: str
    source_system: str
    status: str
    created_at: datetime
    updated_at: datetime
    owner_dept_id: str | None = None
    department_info: dict | None = Field(
        default=None,
        description="Resolved Department entity from erp_qms_core (populated at read time)",
    )

    model_config = ConfigDict(from_attributes=True)


class AuditCacheResponse(BaseModel):
    """AuditCache record enriched with resolved ERP Customer info."""
    id: str
    cache_key: str
    document_id: str
    llm_enabled: bool
    created_at: datetime
    customer_id: str | None = None
    customer_info: dict | None = Field(
        default=None,
        description="Resolved Customer entity from erp_qms_core (populated at read time)",
    )

    model_config = ConfigDict(from_attributes=True)


class CompareCacheResponse(BaseModel):
    """CompareCache record enriched with resolved ERP Supplier info."""
    id: str
    cache_key: str
    left_document_id: str
    right_document_id: str
    use_llm: bool
    created_at: datetime
    supplier_id: str | None = None
    supplier_info: dict | None = Field(
        default=None,
        description="Resolved Supplier entity from erp_qms_core (populated at read time)",
    )

    model_config = ConfigDict(from_attributes=True)
