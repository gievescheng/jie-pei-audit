from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends

from ...core.security import require_roles
from ...schemas.documents import QmsDocumentCreate, QmsDocumentUpdate
from ...services import documents as svc

router = APIRouter()


@router.get("/documents", dependencies=[Depends(require_roles())])
def list_documents():
    return svc.list_documents()


@router.post("/documents", status_code=201, dependencies=[Depends(require_roles("admin", "qm"))])
def create_document(payload: QmsDocumentCreate):
    return svc.create_document(payload)


@router.post("/documents/bulk", status_code=201, dependencies=[Depends(require_roles("admin", "qm"))])
def bulk_upsert(items: List[QmsDocumentCreate]):
    return svc.bulk_upsert([i.model_dump() for i in items])


@router.get("/documents/{document_id}", dependencies=[Depends(require_roles())])
def get_document(document_id: str):
    return svc.get_document(document_id)


@router.put("/documents/{document_id}", dependencies=[Depends(require_roles("admin", "qm"))])
def update_document(document_id: str, payload: QmsDocumentUpdate):
    return svc.update_document(document_id, payload)


@router.delete("/documents/{document_id}", dependencies=[Depends(require_roles("admin", "qm"))])
def delete_document(document_id: str):
    return svc.delete_document(document_id)
