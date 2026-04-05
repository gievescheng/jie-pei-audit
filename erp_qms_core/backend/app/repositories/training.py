from __future__ import annotations

from sqlalchemy.orm import Session

from ..models.training import TrainingEmployee, TrainingRecord


# ── Employees ─────────────────────────────────────────────────────────────────

def list_employees(session: Session) -> list[TrainingEmployee]:
    return (
        session.query(TrainingEmployee)
        .filter(TrainingEmployee.is_deleted == False)  # noqa: E712
        .order_by(TrainingEmployee.emp_no.asc())
        .all()
    )


def get_employee(session: Session, employee_id: str) -> TrainingEmployee | None:
    return (
        session.query(TrainingEmployee)
        .filter(
            TrainingEmployee.id == employee_id,
            TrainingEmployee.is_deleted == False,  # noqa: E712
        )
        .first()
    )


def get_employee_by_no(session: Session, emp_no: str) -> TrainingEmployee | None:
    return (
        session.query(TrainingEmployee)
        .filter(
            TrainingEmployee.emp_no == emp_no,
            TrainingEmployee.is_deleted == False,  # noqa: E712
        )
        .first()
    )


def create_employee(session: Session, **kwargs) -> TrainingEmployee:
    row = TrainingEmployee(**kwargs)
    session.add(row)
    session.flush()
    return row


def update_employee(session: Session, employee_id: str, **kwargs) -> TrainingEmployee | None:
    row = get_employee(session, employee_id)
    if not row:
        return None
    for k, v in kwargs.items():
        if v is not None:
            setattr(row, k, v)
    session.flush()
    return row


# ── Records ───────────────────────────────────────────────────────────────────

def list_records(
    session: Session, employee_id: str | None = None
) -> list[TrainingRecord]:
    q = (
        session.query(TrainingRecord)
        .filter(TrainingRecord.is_deleted == False)  # noqa: E712
    )
    if employee_id:
        q = q.filter(TrainingRecord.employee_id == employee_id)
    return q.order_by(TrainingRecord.training_date.desc()).all()


def get_record(session: Session, record_id: str) -> TrainingRecord | None:
    return (
        session.query(TrainingRecord)
        .filter(
            TrainingRecord.id == record_id,
            TrainingRecord.is_deleted == False,  # noqa: E712
        )
        .first()
    )


def create_record(session: Session, **kwargs) -> TrainingRecord:
    row = TrainingRecord(**kwargs)
    session.add(row)
    session.flush()
    return row


def update_record(session: Session, record_id: str, **kwargs) -> TrainingRecord | None:
    row = get_record(session, record_id)
    if not row:
        return None
    for k, v in kwargs.items():
        if v is not None:
            setattr(row, k, v)
    session.flush()
    return row
