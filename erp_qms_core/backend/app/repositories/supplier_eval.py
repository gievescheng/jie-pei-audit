from __future__ import annotations
from sqlalchemy.orm import Session
from ..models.supplier_eval import SupplierEvaluation


def list_evaluations(session: Session, supplier_id: str | None = None) -> list[SupplierEvaluation]:
    q = (
        session.query(SupplierEvaluation)
        .filter(SupplierEvaluation.is_deleted == False)  # noqa: E712
    )
    if supplier_id:
        q = q.filter(SupplierEvaluation.supplier_id == supplier_id)
    return q.order_by(SupplierEvaluation.eval_date.desc()).all()


def get_evaluation(session: Session, eval_id: str) -> SupplierEvaluation | None:
    return (
        session.query(SupplierEvaluation)
        .filter(SupplierEvaluation.id == eval_id, SupplierEvaluation.is_deleted == False)  # noqa: E712
        .first()
    )


def create_evaluation(session: Session, **kwargs) -> SupplierEvaluation:
    row = SupplierEvaluation(**kwargs)
    session.add(row)
    session.flush()
    return row


def update_evaluation(session: Session, eval_id: str, **kwargs) -> SupplierEvaluation | None:
    row = get_evaluation(session, eval_id)
    if not row:
        return None
    for k, v in kwargs.items():
        if v is not None:
            setattr(row, k, v)
    session.flush()
    return row
