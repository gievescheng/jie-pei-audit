from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.exc import IntegrityError

from ..core.db import session_scope
from ..core.errors import integrity_http_error, not_found_error
from ..core.responses import ok
from ..repositories import training as repo
from ..schemas.training import (
    TrainingEmployeeCreate,
    TrainingEmployeeUpdate,
    TrainingRecordCreate,
    TrainingRecordUpdate,
)


def _record_dict(r) -> dict:
    # 計算是否已過期（validity_months > 0 且有 training_date）
    expired = False
    expiry_date = None
    if r.validity_months and r.validity_months > 0 and r.training_date:
        try:
            d = date.fromisoformat(r.training_date)
            exp = d + timedelta(days=r.validity_months * 30)
            expiry_date = exp.isoformat()
            expired = exp < date.today()
        except ValueError:
            pass
    return {
        "id":              r.id,
        "employee_id":     r.employee_id,
        "course_name":     r.course_name,
        "training_date":   r.training_date,
        "training_type":   r.training_type,
        "result":          r.result,
        "certificate_no":  r.certificate_no,
        "validity_months": r.validity_months,
        "expiry_date":     expiry_date,
        "expired":         expired,
        "remarks":         r.remarks,
        "created_at":      r.created_at.isoformat() if r.created_at else None,
    }


def _employee_dict(emp) -> dict:
    records = [_record_dict(r) for r in emp.records]
    expired_count = sum(1 for r in records if r["expired"])
    return {
        "id":            emp.id,
        "emp_no":        emp.emp_no,
        "emp_name":      emp.emp_name,
        "department":    emp.department,
        "role":          emp.role,
        "hire_date":     emp.hire_date,
        "status":        emp.status,
        "record_count":  len(records),
        "expired_count": expired_count,
        "records":       records,
    }


# ── Employees ─────────────────────────────────────────────────────────────────

def list_employees() -> dict:
    with session_scope() as session:
        rows = repo.list_employees(session)
        return ok([_employee_dict(r) for r in rows])


def get_employee(employee_id: str) -> dict:
    with session_scope() as session:
        row = repo.get_employee(session, employee_id)
        if not row:
            raise not_found_error("training_employee")
        return ok(_employee_dict(row))


def create_employee(payload: TrainingEmployeeCreate) -> dict:
    try:
        with session_scope() as session:
            row = repo.create_employee(session, **payload.model_dump())
            return ok({"id": row.id, "emp_no": row.emp_no}, message="created")
    except IntegrityError as exc:
        raise integrity_http_error(exc) from exc


def update_employee(employee_id: str, payload: TrainingEmployeeUpdate) -> dict:
    with session_scope() as session:
        data = {k: v for k, v in payload.model_dump().items() if v is not None}
        row = repo.update_employee(session, employee_id, **data)
        if not row:
            raise not_found_error("training_employee")
        return ok(_employee_dict(row), message="updated")


def delete_employee(employee_id: str) -> dict:
    with session_scope() as session:
        row = repo.get_employee(session, employee_id)
        if not row:
            raise not_found_error("training_employee")
        row.is_deleted = True
        return ok({"id": row.id}, message="deleted")


def bulk_seed_employees(items: list[dict]) -> dict:
    """批量種入員工資料（emp_no 相同則略過）。"""
    created = 0
    with session_scope() as session:
        for item in items:
            emp_no = item.get("emp_no", "")
            if not emp_no:
                continue
            existing = repo.get_employee_by_no(session, emp_no)
            if not existing:
                from ..models.training import TrainingEmployee
                session.add(TrainingEmployee(**{k: v for k, v in item.items() if k != "records"}))
                session.flush()
                created += 1
    return ok({"created": created}, message="bulk_seed done")


# ── Records ───────────────────────────────────────────────────────────────────

def list_records(employee_id: str | None = None) -> dict:
    with session_scope() as session:
        rows = repo.list_records(session, employee_id=employee_id)
        return ok([_record_dict(r) for r in rows])


def create_record(payload: TrainingRecordCreate) -> dict:
    try:
        with session_scope() as session:
            row = repo.create_record(session, **payload.model_dump())
            return ok(_record_dict(row), message="created")
    except IntegrityError as exc:
        raise integrity_http_error(exc) from exc


def update_record(record_id: str, payload: TrainingRecordUpdate) -> dict:
    with session_scope() as session:
        data = {k: v for k, v in payload.model_dump().items() if v is not None}
        row = repo.update_record(session, record_id, **data)
        if not row:
            raise not_found_error("training_record")
        return ok(_record_dict(row), message="updated")


def delete_record(record_id: str) -> dict:
    with session_scope() as session:
        row = repo.get_record(session, record_id)
        if not row:
            raise not_found_error("training_record")
        row.is_deleted = True
        return ok({"id": row.id}, message="deleted")
