from __future__ import annotations

from sqlalchemy.exc import IntegrityError

from ..core.db import session_scope
from ..core.errors import integrity_http_error, not_found_error
from ..core.responses import ok
from ..repositories import products as repo
from ..schemas.master import MaterialMasterCreate, MaterialMasterUpdate, ShiftMasterCreate
from ..schemas.products import ProductCreate, ProductUpdate


# ── Products ─────────────────────────────────────────────────

def list_products() -> dict:
    with session_scope() as session:
        rows = repo.list_all(session)
        return ok([
            {"id": r.id, "product_code": r.product_code, "product_name": r.product_name,
             "customer_part_no": r.customer_part_no, "internal_part_no": r.internal_part_no,
             "status": r.status}
            for r in rows
        ])


def get_product(product_id: str) -> dict:
    with session_scope() as session:
        row = repo.get_by_id(session, product_id)
        if not row:
            raise not_found_error("product")
        return ok({"id": row.id, "product_code": row.product_code, "product_name": row.product_name,
                   "customer_part_no": row.customer_part_no, "internal_part_no": row.internal_part_no,
                   "spec_summary": row.spec_summary, "status": row.status})


def create_product(payload: ProductCreate) -> dict:
    try:
        with session_scope() as session:
            row = repo.create(session,
                              product_code=payload.product_code,
                              product_name=payload.product_name,
                              customer_part_no=payload.customer_part_no,
                              internal_part_no=payload.internal_part_no,
                              spec_summary=payload.spec_summary)
            return ok({"id": row.id, "product_code": row.product_code, "product_name": row.product_name},
                      message="created")
    except IntegrityError as exc:
        raise integrity_http_error(exc) from exc


def update_product(product_id: str, payload: ProductUpdate) -> dict:
    with session_scope() as session:
        row = repo.get_by_id(session, product_id)
        if not row:
            raise not_found_error("product")
        for field in ("product_name", "customer_part_no", "internal_part_no", "spec_summary", "status"):
            val = getattr(payload, field)
            if val is not None:
                setattr(row, field, val)
        return ok({"id": row.id, "product_code": row.product_code,
                   "product_name": row.product_name, "status": row.status}, message="updated")


# ── Materials ────────────────────────────────────────────────

def list_materials() -> dict:
    with session_scope() as session:
        rows = repo.list_materials(session)
        return ok([
            {"id": r.id, "material_code": r.material_code, "material_name": r.material_name,
             "material_type": r.material_type, "unit": r.unit, "status": r.status}
            for r in rows
        ])


def get_material(material_id: str) -> dict:
    with session_scope() as session:
        row = repo.get_material_by_id(session, material_id)
        if not row:
            raise not_found_error("material")
        return ok({"id": row.id, "material_code": row.material_code, "material_name": row.material_name,
                   "material_type": row.material_type, "unit": row.unit, "status": row.status})


def create_material(payload: MaterialMasterCreate) -> dict:
    try:
        with session_scope() as session:
            row = repo.create_material(session,
                                       material_code=payload.material_code,
                                       material_name=payload.material_name,
                                       material_type=payload.material_type,
                                       unit=payload.unit)
            return ok({"id": row.id, "material_code": row.material_code, "material_name": row.material_name},
                      message="created")
    except IntegrityError as exc:
        raise integrity_http_error(exc) from exc


def update_material(material_id: str, payload: MaterialMasterUpdate) -> dict:
    with session_scope() as session:
        row = repo.get_material_by_id(session, material_id)
        if not row:
            raise not_found_error("material")
        for field in ("material_name", "material_type", "unit", "status"):
            val = getattr(payload, field)
            if val is not None:
                setattr(row, field, val)
        return ok({"id": row.id, "material_code": row.material_code,
                   "material_name": row.material_name, "status": row.status}, message="updated")


# ── Shifts ───────────────────────────────────────────────────

def list_shifts() -> dict:
    with session_scope() as session:
        rows = repo.list_shifts(session)
        return ok([
            {"id": r.id, "shift_code": r.shift_code, "shift_name": r.shift_name,
             "start_time": r.start_time, "end_time": r.end_time}
            for r in rows
        ])


def create_shift(payload: ShiftMasterCreate) -> dict:
    try:
        with session_scope() as session:
            row = repo.create_shift(session,
                                    shift_code=payload.shift_code,
                                    shift_name=payload.shift_name,
                                    start_time=payload.start_time,
                                    end_time=payload.end_time)
            return ok({"id": row.id, "shift_code": row.shift_code, "shift_name": row.shift_name},
                      message="created")
    except IntegrityError as exc:
        raise integrity_http_error(exc) from exc
