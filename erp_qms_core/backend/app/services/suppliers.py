from __future__ import annotations

from sqlalchemy.exc import IntegrityError

from ..core.db import session_scope
from ..core.errors import integrity_http_error, not_found_error
from ..core.responses import ok
from ..repositories import suppliers as repo
from ..schemas.suppliers import SupplierCreate, SupplierUpdate


def list_suppliers() -> dict:
    with session_scope() as session:
        rows = repo.list_all(session)
        return ok([
            {"id": r.id, "supplier_code": r.supplier_code, "supplier_name": r.supplier_name,
             "category": r.category, "status": r.status}
            for r in rows
        ])


def get_supplier(supplier_id: str) -> dict:
    with session_scope() as session:
        row = repo.get_by_id(session, supplier_id)
        if not row:
            raise not_found_error("supplier")
        return ok({"id": row.id, "supplier_code": row.supplier_code, "supplier_name": row.supplier_name,
                   "category": row.category, "status": row.status})


def create_supplier(payload: SupplierCreate) -> dict:
    try:
        with session_scope() as session:
            row = repo.create(session, payload.supplier_code, payload.supplier_name, payload.category)
            return ok({"id": row.id, "supplier_code": row.supplier_code, "supplier_name": row.supplier_name},
                      message="created")
    except IntegrityError as exc:
        raise integrity_http_error(exc) from exc


def update_supplier(supplier_id: str, payload: SupplierUpdate) -> dict:
    with session_scope() as session:
        row = repo.get_by_id(session, supplier_id)
        if not row:
            raise not_found_error("supplier")
        if payload.supplier_name is not None:
            row.supplier_name = payload.supplier_name
        if payload.category is not None:
            row.category = payload.category
        if payload.status is not None:
            row.status = payload.status
        return ok({"id": row.id, "supplier_code": row.supplier_code,
                   "supplier_name": row.supplier_name, "status": row.status}, message="updated")
