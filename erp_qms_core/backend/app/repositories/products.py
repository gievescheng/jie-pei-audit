from __future__ import annotations

from sqlalchemy.orm import Session

from ..models.master import MaterialMaster, Product, ShiftMaster


def list_all(session: Session) -> list[Product]:
    return (
        session.query(Product)
        .filter(Product.is_deleted == False)  # noqa: E712
        .order_by(Product.product_code.asc())
        .all()
    )


def get_by_id(session: Session, product_id: str) -> Product | None:
    return (
        session.query(Product)
        .filter(Product.id == product_id, Product.is_deleted == False)  # noqa: E712
        .first()
    )


def create(session: Session, **kwargs) -> Product:
    row = Product(**kwargs)
    session.add(row)
    session.flush()
    return row


# ── Material ─────────────────────────────────────────────────

def list_materials(session: Session) -> list[MaterialMaster]:
    return (
        session.query(MaterialMaster)
        .filter(MaterialMaster.is_deleted == False)  # noqa: E712
        .order_by(MaterialMaster.material_code.asc())
        .all()
    )


def get_material_by_id(session: Session, material_id: str) -> MaterialMaster | None:
    return (
        session.query(MaterialMaster)
        .filter(MaterialMaster.id == material_id, MaterialMaster.is_deleted == False)  # noqa: E712
        .first()
    )


def create_material(session: Session, **kwargs) -> MaterialMaster:
    row = MaterialMaster(**kwargs)
    session.add(row)
    session.flush()
    return row


# ── Shift ────────────────────────────────────────────────────

def list_shifts(session: Session) -> list[ShiftMaster]:
    return (
        session.query(ShiftMaster)
        .filter(ShiftMaster.is_deleted == False)  # noqa: E712
        .order_by(ShiftMaster.shift_code.asc())
        .all()
    )


def create_shift(session: Session, **kwargs) -> ShiftMaster:
    row = ShiftMaster(**kwargs)
    session.add(row)
    session.flush()
    return row
