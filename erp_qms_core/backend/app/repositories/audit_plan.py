from __future__ import annotations

from sqlalchemy.orm import Session

from ..models.audit_plan import AuditPlan


def list_all(session: Session) -> list[AuditPlan]:
    return (
        session.query(AuditPlan)
        .filter(AuditPlan.is_deleted == False)  # noqa: E712
        .order_by(AuditPlan.scheduled_date.desc(), AuditPlan.plan_no.desc())
        .all()
    )


def get_by_no(session: Session, plan_no: str) -> AuditPlan | None:
    return (
        session.query(AuditPlan)
        .filter(AuditPlan.plan_no == plan_no, AuditPlan.is_deleted == False)  # noqa: E712
        .first()
    )


def count_all(session: Session) -> int:
    return session.query(AuditPlan).filter(AuditPlan.is_deleted == False).count()  # noqa: E712


def create(session: Session, **kwargs) -> AuditPlan:
    row = AuditPlan(**kwargs)
    session.add(row)
    session.flush()
    return row


def update(session: Session, plan_no: str, **kwargs) -> AuditPlan | None:
    row = get_by_no(session, plan_no)
    if not row:
        return None
    for k, v in kwargs.items():
        setattr(row, k, v)
    session.flush()
    return row


def soft_delete(session: Session, plan_no: str) -> bool:
    row = get_by_no(session, plan_no)
    if not row:
        return False
    row.is_deleted = True
    session.flush()
    return True


def bulk_seed(session: Session, rows: list[dict]) -> int:
    existing = {r.plan_no for r in session.query(AuditPlan.plan_no).filter(AuditPlan.is_deleted == False).all()}  # noqa: E712
    added = 0
    for row in rows:
        if row.get("plan_no") in existing:
            continue
        session.add(AuditPlan(**row))
        existing.add(row["plan_no"])
        added += 1
    if added:
        session.flush()
    return added
