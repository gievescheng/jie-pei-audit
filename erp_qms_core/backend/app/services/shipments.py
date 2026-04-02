from __future__ import annotations

from sqlalchemy.exc import IntegrityError

from fastapi import HTTPException

from ..core.db import session_scope
from ..core.errors import integrity_http_error, not_found_error
from ..domain.transitions import can_transition
from ..core.responses import ok
from ..repositories import shipments as repo
from ..schemas.common import StatusUpdate
from ..schemas.shipments import ShipmentCreate


def list_shipments() -> dict:
    with session_scope() as session:
        rows = repo.list_all(session)
        return ok([
            {"id": r.id, "shipment_no": r.shipment_no, "so_id": r.so_id,
             "shipment_date": str(r.shipment_date) if r.shipment_date else None,
             "ship_status": r.ship_status}
            for r in rows
        ])


def get_shipment(shipment_id: str) -> dict:
    with session_scope() as session:
        row = repo.get_by_id(session, shipment_id)
        if not row:
            raise not_found_error("shipment")
        return ok({"id": row.id, "shipment_no": row.shipment_no, "so_id": row.so_id,
                   "shipment_date": str(row.shipment_date) if row.shipment_date else None,
                   "ship_status": row.ship_status, "remark": row.remark})


def create_shipment(payload: ShipmentCreate) -> dict:
    try:
        with session_scope() as session:
            row = repo.create(session,
                              shipment_no=payload.shipment_no,
                              so_id=payload.so_id,
                              shipment_date=payload.shipment_date,
                              ship_status=payload.ship_status,
                              remark=payload.remark)
            return ok({"id": row.id, "shipment_no": row.shipment_no, "ship_status": row.ship_status},
                      message="created")
    except IntegrityError as exc:
        raise integrity_http_error(exc) from exc


def update_shipment_status(shipment_id: str, payload: StatusUpdate) -> dict:
    with session_scope() as session:
        row = repo.get_by_id(session, shipment_id)
        if not row:
            raise not_found_error("shipment")
        if not can_transition("shipment", row.ship_status, payload.status):
            raise HTTPException(
                status_code=422,
                detail=f"無法從 '{row.ship_status}' 轉換為 '{payload.status}'。請確認出貨目前狀態允許此操作。",
            )
        row.ship_status = payload.status
        return ok({"id": row.id, "shipment_no": row.shipment_no, "ship_status": row.ship_status}, message="updated")
