from __future__ import annotations

from sqlalchemy.orm import Session

from ..models.documents import QmsDocument


def list_documents(session: Session) -> list[QmsDocument]:
    return (
        session.query(QmsDocument)
        .filter(QmsDocument.is_deleted == False)  # noqa: E712
        .order_by(QmsDocument.doc_no.asc())
        .all()
    )


def get_document(session: Session, document_id: str) -> QmsDocument | None:
    return (
        session.query(QmsDocument)
        .filter(
            QmsDocument.id == document_id,
            QmsDocument.is_deleted == False,  # noqa: E712
        )
        .first()
    )


def get_document_by_no(session: Session, doc_no: str) -> QmsDocument | None:
    return (
        session.query(QmsDocument)
        .filter(
            QmsDocument.doc_no == doc_no,
            QmsDocument.is_deleted == False,  # noqa: E712
        )
        .first()
    )


def create_document(session: Session, **kwargs) -> QmsDocument:
    row = QmsDocument(**kwargs)
    session.add(row)
    session.flush()
    return row


def update_document(session: Session, document_id: str, **kwargs) -> QmsDocument | None:
    row = get_document(session, document_id)
    if not row:
        return None
    for k, v in kwargs.items():
        if v is not None:
            setattr(row, k, v)
    session.flush()
    return row
