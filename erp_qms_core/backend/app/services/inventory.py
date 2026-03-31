from __future__ import annotations

from sqlalchemy.exc import IntegrityError

from ..core.db import session_scope
from ..core.errors import integrity_http_error
from ..core.responses import ok
from ..repositories import inventory as repo
from ..schemas.inventory import InventoryLocationCreate, InventoryTransactionCreate


def list_locations() -> dict:
    with session_scope() as session:
        rows = repo.list_locations(session)
        return ok([
            {"id": r.id, "location_code": r.location_code, "location_name": r.location_name,
             "location_type": r.location_type, "is_hold_area": r.is_hold_area}
            for r in rows
        ])


def create_location(payload: InventoryLocationCreate) -> dict:
    try:
        with session_scope() as session:
            row = repo.create_location(session,
                                       location_code=payload.location_code,
                                       location_name=payload.location_name,
                                       location_type=payload.location_type,
                                       is_hold_area=payload.is_hold_area)
            return ok({"id": row.id, "location_code": row.location_code, "location_name": row.location_name},
                      message="created")
    except IntegrityError as exc:
        raise integrity_http_error(exc) from exc


def list_transactions() -> dict:
    with session_scope() as session:
        rows = repo.list_transactions(session)
        return ok([
            {"id": r.id, "trx_no": r.trx_no, "trx_type": r.trx_type, "lot_no": r.lot_no,
             "qty": float(r.qty), "location_code": r.location_code,
             "inventory_status": r.inventory_status,
             "trx_date": str(r.trx_date) if r.trx_date else None}
            for r in rows
        ])


def create_transaction(payload: InventoryTransactionCreate) -> dict:
    try:
        with session_scope() as session:
            row = repo.create_transaction(session,
                                          trx_no=payload.trx_no,
                                          trx_type=payload.trx_type,
                                          item_type=payload.item_type,
                                          item_ref_id=payload.item_ref_id,
                                          lot_no=payload.lot_no,
                                          qty=payload.qty,
                                          location_code=payload.location_code,
                                          inventory_status=payload.inventory_status,
                                          trx_date=payload.trx_date)
            return ok({"id": row.id, "trx_no": row.trx_no,
                       "trx_type": row.trx_type, "qty": float(row.qty)}, message="created")
    except IntegrityError as exc:
        raise integrity_http_error(exc) from exc
