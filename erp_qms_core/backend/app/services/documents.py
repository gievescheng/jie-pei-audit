from __future__ import annotations

from sqlalchemy.exc import IntegrityError

from ..core.db import session_scope
from ..core.errors import integrity_http_error, not_found_error
from ..core.responses import ok
from ..repositories import documents as repo
from ..schemas.documents import QmsDocumentCreate, QmsDocumentUpdate


def _doc_dict(row) -> dict:
    return {
        "id":              row.id,
        "doc_no":          row.doc_no,
        "doc_name":        row.doc_name,
        "doc_type":        row.doc_type,
        "version":         row.version,
        "department":      row.department,
        "author":          row.author,
        "issue_date":      row.issue_date,
        "retention_years": row.retention_years,
        "pdf_path":        row.pdf_path,
        "docx_path":       row.docx_path,
        "remarks":         row.remarks,
        "created_at":      row.created_at.isoformat() if row.created_at else None,
        "updated_at":      row.updated_at.isoformat() if row.updated_at else None,
    }


def list_documents() -> dict:
    with session_scope() as session:
        rows = repo.list_documents(session)
        return ok([_doc_dict(r) for r in rows])


def get_document(document_id: str) -> dict:
    with session_scope() as session:
        row = repo.get_document(session, document_id)
        if not row:
            raise not_found_error("qms_document")
        return ok(_doc_dict(row))


def create_document(payload: QmsDocumentCreate) -> dict:
    try:
        with session_scope() as session:
            row = repo.create_document(session, **payload.model_dump())
            return ok({"id": row.id, "doc_no": row.doc_no}, message="created")
    except IntegrityError as exc:
        raise integrity_http_error(exc) from exc


def update_document(document_id: str, payload: QmsDocumentUpdate) -> dict:
    with session_scope() as session:
        data = {k: v for k, v in payload.model_dump().items() if v is not None}
        row = repo.update_document(session, document_id, **data)
        if not row:
            raise not_found_error("qms_document")
        return ok(_doc_dict(row), message="updated")


def delete_document(document_id: str) -> dict:
    with session_scope() as session:
        row = repo.get_document(session, document_id)
        if not row:
            raise not_found_error("qms_document")
        row.is_deleted = True
        return ok({"id": row.id}, message="deleted")


def bulk_upsert(items: list[dict]) -> dict:
    """批量匯入文件（doc_no 相同則更新，否則新增）。"""
    created = updated = 0
    with session_scope() as session:
        for item in items:
            doc_no = item.get("doc_no", "")
            if not doc_no:
                continue
            existing = repo.get_document_by_no(session, doc_no)
            if existing:
                for k, v in item.items():
                    if k != "doc_no" and v is not None:
                        setattr(existing, k, v)
                session.flush()
                updated += 1
            else:
                session.add(__import__("app.models.documents", fromlist=["QmsDocument"]).QmsDocument(**item))
                session.flush()
                created += 1
    return ok({"created": created, "updated": updated}, message="bulk_upsert done")
