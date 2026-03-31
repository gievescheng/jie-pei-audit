from __future__ import annotations

from sqlalchemy.exc import IntegrityError

from ..core.db import session_scope
from ..core.errors import integrity_http_error, not_found_error
from ..core.responses import ok
from ..repositories import customers as repo
from ..schemas.customers import CustomerCreate, CustomerUpdate


def list_customers() -> dict:
    with session_scope() as session:
        rows = repo.list_all(session)
        return ok([
            {"id": r.id, "customer_code": r.customer_code, "customer_name": r.customer_name,
             "short_name": r.short_name, "status": r.status}
            for r in rows
        ])


def get_customer(customer_id: str) -> dict:
    with session_scope() as session:
        row = repo.get_by_id(session, customer_id)
        if not row:
            raise not_found_error("customer")
        return ok({"id": row.id, "customer_code": row.customer_code, "customer_name": row.customer_name,
                   "short_name": row.short_name, "status": row.status})


def create_customer(payload: CustomerCreate) -> dict:
    try:
        with session_scope() as session:
            row = repo.create(session, payload.customer_code, payload.customer_name, payload.short_name)
            return ok({"id": row.id, "customer_code": row.customer_code, "customer_name": row.customer_name},
                      message="created")
    except IntegrityError as exc:
        raise integrity_http_error(exc) from exc


def update_customer(customer_id: str, payload: CustomerUpdate) -> dict:
    with session_scope() as session:
        row = repo.get_by_id(session, customer_id)
        if not row:
            raise not_found_error("customer")
        if payload.customer_name is not None:
            row.customer_name = payload.customer_name
        if payload.short_name is not None:
            row.short_name = payload.short_name
        if payload.status is not None:
            row.status = payload.status
        return ok({"id": row.id, "customer_code": row.customer_code,
                   "customer_name": row.customer_name, "status": row.status}, message="updated")
