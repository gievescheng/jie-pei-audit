from __future__ import annotations

from sqlalchemy.orm import Session

from ..models.nonconformance import NonConformance


def list_all(session: Session) -> list[NonConformance]:
    return (
        session.query(NonConformance)
        .filter(NonConformance.is_deleted == False)  # noqa: E712
        .order_by(NonConformance.nc_date.desc(), NonConformance.nc_no.desc())
        .all()
    )


def get_by_no(session: Session, nc_no: str) -> NonConformance | None:
    return (
        session.query(NonConformance)
        .filter(NonConformance.nc_no == nc_no, NonConformance.is_deleted == False)  # noqa: E712
        .first()
    )


def count_all(session: Session) -> int:
    return session.query(NonConformance).filter(NonConformance.is_deleted == False).count()  # noqa: E712


def create(session: Session, **kwargs) -> NonConformance:
    row = NonConformance(**kwargs)
    session.add(row)
    session.flush()
    return row


def update(session: Session, nc_no: str, **kwargs) -> NonConformance | None:
    row = get_by_no(session, nc_no)
    if not row:
        return None
    for k, v in kwargs.items():
        setattr(row, k, v)
    session.flush()
    return row


def soft_delete(session: Session, nc_no: str) -> bool:
    row = get_by_no(session, nc_no)
    if not row:
        return False
    row.is_deleted = True
    session.flush()
    return True


def bulk_seed(session: Session, rows: list[dict]) -> int:
    existing = {r.nc_no for r in session.query(NonConformance.nc_no).filter(NonConformance.is_deleted == False).all()}  # noqa: E712
    added = 0
    for row in rows:
        if row.get("nc_no") in existing:
            continue
        session.add(NonConformance(**row))
        existing.add(row["nc_no"])
        added += 1
    if added:
        session.flush()
    return added
