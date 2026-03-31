from __future__ import annotations

from sqlalchemy.orm import Session

from ..models.master import Supplier


def list_all(session: Session) -> list[Supplier]:
    return (
        session.query(Supplier)
        .filter(Supplier.is_deleted == False)  # noqa: E712
        .order_by(Supplier.supplier_code.asc())
        .all()
    )


def get_by_id(session: Session, supplier_id: str) -> Supplier | None:
    return (
        session.query(Supplier)
        .filter(Supplier.id == supplier_id, Supplier.is_deleted == False)  # noqa: E712
        .first()
    )


def create(session: Session, supplier_code: str, supplier_name: str, category: str = "") -> Supplier:
    row = Supplier(supplier_code=supplier_code, supplier_name=supplier_name, category=category)
    session.add(row)
    session.flush()
    return row
