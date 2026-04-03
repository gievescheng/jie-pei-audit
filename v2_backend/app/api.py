from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from .audit import write_audit_log
from .auth import require_api_key
from .config import settings
from .db import get_database_status, session_scope
from .exports import build_document_audit_docx, build_document_compare_docx, build_document_compare_workbook
from .schemas import DeviationDraftRequest, DocumentAuditRequest, DocumentCompareRequest, DocumentIngestRequest, DocumentVersionCandidatesRequest, KnowledgeQARequest, SPCAnalyzeRequest
from .services import analyze_spc, answer_knowledge_question, audit_document, clear_runtime_cache, compare_documents, draft_deviation, ensure_seed_prompts, get_runtime_cache_status, ingest_documents, list_result_history, resolve_prompt, search_documents, suggest_version_candidates

router = APIRouter(prefix="/api/v2", tags=["v2"], dependencies=[Depends(require_api_key)])



def _ok(data, *, message="OK", trace_id=None):
    return {
        "success": True,
        "data": data,
        "error_code": "",
        "message": message,
        "trace_id": trace_id or str(uuid.uuid4()),
    }



def _error(message, *, error_code="bad_request", trace_id=None):
    return {
        "success": False,
        "data": None,
        "error_code": error_code,
        "message": message,
        "trace_id": trace_id or str(uuid.uuid4()),
    }


@router.get("/health")
def health():
    db_status = get_database_status()
    return _ok(
        {
            "service": "auto-audit-v2",
            "database_mode": db_status["active_database_mode"],
            "database_status": db_status,
            "openrouter_enabled": bool(settings.openrouter_api_key),
        },
        message="healthy",
    )


@router.get("/cache/status")
def cache_status():
    trace_id = str(uuid.uuid4())
    try:
        with session_scope() as session:
            data = get_runtime_cache_status(session)
        return _ok(data, message="cache status", trace_id=trace_id)
    except Exception as exc:
        return _error(str(exc), error_code="cache_status_failed", trace_id=trace_id)


@router.post("/cache/clear")
def cache_clear(target: str = Query("all")):
    trace_id = str(uuid.uuid4())
    try:
        with session_scope() as session:
            data = clear_runtime_cache(session, target=target)
            write_audit_log(
                session,
                trace_id=trace_id,
                task_type="cache_clear",
                prompt_version="",
                result_status="success",
                request_summary=json.dumps({"target": target}, ensure_ascii=False),
            )
        return _ok(data, message="cache cleared", trace_id=trace_id)
    except Exception as exc:
        return _error(str(exc), error_code="cache_clear_failed", trace_id=trace_id)


@router.get("/history/runs")
def history_runs(mode: str = Query("all"), q: str = Query(""), limit: int = Query(20, ge=1, le=100)):
    trace_id = str(uuid.uuid4())
    try:
        with session_scope() as session:
            data = list_result_history(session, mode=mode, query=q, limit=limit)
        return _ok(data, message="history ready", trace_id=trace_id)
    except Exception as exc:
        return _error(str(exc), error_code="history_failed", trace_id=trace_id)


@router.post("/documents/ingest")
def documents_ingest(payload: DocumentIngestRequest):
    trace_id = str(uuid.uuid4())
    try:
        with session_scope() as session:
            ensure_seed_prompts(session)
            data = ingest_documents(session, payload)
            write_audit_log(
                session,
                trace_id=trace_id,
                task_type="doc_ingest",
                prompt_version="",
                result_status="success",
                request_summary=json.dumps({"paths": payload.paths}, ensure_ascii=False)[:500],
            )
        return _ok(data, message="documents ingested", trace_id=trace_id)
    except Exception as exc:
        with session_scope() as session:
            write_audit_log(
                session,
                trace_id=trace_id,
                task_type="doc_ingest",
                prompt_version="",
                result_status="error",
                request_summary=json.dumps({"paths": payload.paths}, ensure_ascii=False)[:500],
            )
        return _error(str(exc), error_code="ingest_failed", trace_id=trace_id)


@router.get("/documents/search")
def documents_search(q: str = Query("", min_length=1), limit: int = Query(8, ge=1, le=30)):
    trace_id = str(uuid.uuid4())
    try:
        with session_scope() as session:
            ensure_seed_prompts(session)
            data = search_documents(session, q, limit=limit)
            write_audit_log(
                session,
                trace_id=trace_id,
                task_type="doc_search",
                prompt_version="",
                result_status="success",
                request_summary=json.dumps({"q": q, "limit": limit}, ensure_ascii=False),
            )
        return _ok(data, message="search complete", trace_id=trace_id)
    except Exception as exc:
        return _error(str(exc), error_code="search_failed", trace_id=trace_id)


@router.post("/documents/audit")
def documents_audit(payload: DocumentAuditRequest):
    trace_id = str(uuid.uuid4())
    try:
        with session_scope() as session:
            ensure_seed_prompts(session)
            data = audit_document(session, payload)
            write_audit_log(
                session,
                trace_id=trace_id,
                task_type="doc_audit",
                prompt_version=data.get("prompt_version", ""),
                result_status="success",
                request_summary=json.dumps(payload.model_dump(), ensure_ascii=False)[:500],
            )
        return _ok(data, message="document audit complete", trace_id=trace_id)
    except Exception as exc:
        return _error(str(exc), error_code="audit_failed", trace_id=trace_id)


@router.post("/documents/audit/export/docx")
def documents_audit_export_docx(payload: DocumentAuditRequest):
    trace_id = str(uuid.uuid4())
    try:
        with session_scope() as session:
            ensure_seed_prompts(session)
            data = audit_document(session, payload)
            if payload.document_id:
                data["document_path"] = ""
                data["document_title"] = data.get("document_title") or ""
            else:
                data["document_path"] = payload.path or ""
                data["document_title"] = data.get("document_title") or ""
            docx_bytes = build_document_audit_docx(data)
            write_audit_log(
                session,
                trace_id=trace_id,
                task_type="doc_audit_export_docx",
                prompt_version=data.get("prompt_version", ""),
                result_status="success",
                request_summary=json.dumps(payload.model_dump(), ensure_ascii=False)[:500],
            )
        headers = {"Content-Disposition": 'attachment; filename="document_audit_report.docx"'}
        return StreamingResponse(
            iter([docx_bytes]),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers=headers,
        )
    except Exception as exc:
        return _error(str(exc), error_code="audit_export_docx_failed", trace_id=trace_id)


@router.post("/documents/compare")
def documents_compare(payload: DocumentCompareRequest):
    trace_id = str(uuid.uuid4())
    try:
        with session_scope() as session:
            ensure_seed_prompts(session)
            data = compare_documents(session, payload)
            write_audit_log(
                session,
                trace_id=trace_id,
                task_type="doc_compare",
                prompt_version=data.get("prompt_version", ""),
                result_status="success",
                request_summary=json.dumps(payload.model_dump(), ensure_ascii=False)[:500],
            )
        return _ok(data, message="document compare complete", trace_id=trace_id)
    except Exception as exc:
        return _error(str(exc), error_code="compare_failed", trace_id=trace_id)


@router.post("/documents/version-candidates")
def documents_version_candidates(payload: DocumentVersionCandidatesRequest):
    trace_id = str(uuid.uuid4())
    try:
        with session_scope() as session:
            ensure_seed_prompts(session)
            data = suggest_version_candidates(session, payload)
            write_audit_log(
                session,
                trace_id=trace_id,
                task_type="doc_version_candidates",
                prompt_version="",
                result_status="success",
                request_summary=json.dumps(payload.model_dump(), ensure_ascii=False)[:500],
            )
        return _ok(data, message="version candidates ready", trace_id=trace_id)
    except Exception as exc:
        return _error(str(exc), error_code="version_candidates_failed", trace_id=trace_id)


@router.post("/documents/compare/export")
def documents_compare_export(payload: DocumentCompareRequest):
    trace_id = str(uuid.uuid4())
    try:
        with session_scope() as session:
            ensure_seed_prompts(session)
            data = compare_documents(session, payload)
            workbook_bytes = build_document_compare_workbook(data)
            write_audit_log(
                session,
                trace_id=trace_id,
                task_type="doc_compare_export",
                prompt_version=data.get("prompt_version", ""),
                result_status="success",
                request_summary=json.dumps(payload.model_dump(), ensure_ascii=False)[:500],
            )
        headers = {"Content-Disposition": 'attachment; filename="document_compare_report.xlsx"'}
        return StreamingResponse(
            iter([workbook_bytes]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers=headers,
        )
    except Exception as exc:
        return _error(str(exc), error_code="compare_export_failed", trace_id=trace_id)


@router.post("/documents/compare/export/docx")
def documents_compare_export_docx(payload: DocumentCompareRequest):
    trace_id = str(uuid.uuid4())
    try:
        with session_scope() as session:
            ensure_seed_prompts(session)
            data = compare_documents(session, payload)
            docx_bytes = build_document_compare_docx(data)
            write_audit_log(
                session,
                trace_id=trace_id,
                task_type="doc_compare_export_docx",
                prompt_version=data.get("prompt_version", ""),
                result_status="success",
                request_summary=json.dumps(payload.model_dump(), ensure_ascii=False)[:500],
            )
        headers = {"Content-Disposition": 'attachment; filename="document_compare_report.docx"'}
        return StreamingResponse(
            iter([docx_bytes]),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers=headers,
        )
    except Exception as exc:
        return _error(str(exc), error_code="compare_export_docx_failed", trace_id=trace_id)


@router.post("/spc/analyze")
def spc_analyze(payload: SPCAnalyzeRequest):
    trace_id = str(uuid.uuid4())
    try:
        with session_scope() as session:
            ensure_seed_prompts(session)
            data = analyze_spc(session, payload)
            write_audit_log(
                session,
                trace_id=trace_id,
                task_type="spc_analyze",
                prompt_version=data.get("prompt_version", ""),
                result_status="success",
                request_summary=json.dumps(payload.model_dump(), ensure_ascii=False)[:500],
            )
        return _ok(data, message="spc analysis complete", trace_id=trace_id)
    except Exception as exc:
        return _error(str(exc), error_code="spc_failed", trace_id=trace_id)


@router.post("/deviations/draft")
def deviation_draft(payload: DeviationDraftRequest):
    trace_id = str(uuid.uuid4())
    try:
        with session_scope() as session:
            ensure_seed_prompts(session)
            data = draft_deviation(session, payload)
            write_audit_log(
                session,
                trace_id=trace_id,
                task_type="deviation_analyze",
                prompt_version=data.get("prompt_version", ""),
                result_status="success",
                request_summary=json.dumps(payload.model_dump(), ensure_ascii=False)[:500],
            )
        return _ok(data, message="deviation draft complete", trace_id=trace_id)
    except Exception as exc:
        return _error(str(exc), error_code="deviation_failed", trace_id=trace_id)


@router.post("/knowledge/qa")
def knowledge_qa(payload: KnowledgeQARequest):
    trace_id = str(uuid.uuid4())
    try:
        with session_scope() as session:
            ensure_seed_prompts(session)
            data = answer_knowledge_question(session, payload)
            write_audit_log(
                session,
                trace_id=trace_id,
                task_type="knowledge_qa",
                prompt_version=data.get("prompt_version", ""),
                result_status="success",
                request_summary=json.dumps(payload.model_dump(), ensure_ascii=False)[:500],
            )
        return _ok(data, message="knowledge qa complete", trace_id=trace_id)
    except Exception as exc:
        return _error(str(exc), error_code="knowledge_qa_failed", trace_id=trace_id)


@router.get("/prompts/runtime/resolve")
def prompt_runtime_resolve(task_type: str = Query(..., min_length=1)):
    trace_id = str(uuid.uuid4())
    try:
        with session_scope() as session:
            ensure_seed_prompts(session)
            data = resolve_prompt(session, task_type)
        return _ok(data, message="prompt resolved", trace_id=trace_id)
    except Exception as exc:
        return _error(str(exc), error_code="prompt_resolve_failed", trace_id=trace_id)
