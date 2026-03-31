from __future__ import annotations

from sqlalchemy.exc import IntegrityError

from ..core.db import session_scope
from ..core.errors import integrity_http_error, not_found_error
from ..core.responses import ok
from ..repositories import orders as repo
from ..schemas.common import StatusUpdate, WorkOrderQtyUpdate
from ..schemas.orders import WorkOrderCreate


def list_work_orders() -> dict:
    with session_scope() as session:
        rows = repo.list_work_orders(session)
        return ok([
            {"id": r.id, "wo_no": r.wo_no, "so_id": r.so_id, "product_id": r.product_id,
             "planned_qty": float(r.planned_qty), "good_qty": float(r.good_qty),
             "ng_qty": float(r.ng_qty), "wo_status": r.wo_status}
            for r in rows
        ])


def get_work_order(wo_id: str) -> dict:
    with session_scope() as session:
        row = repo.get_work_order(session, wo_id)
        if not row:
            raise not_found_error("work order")
        return ok({
            "id": row.id, "wo_no": row.wo_no, "so_id": row.so_id, "product_id": row.product_id,
            "planned_qty": float(row.planned_qty), "released_qty": float(row.released_qty),
            "good_qty": float(row.good_qty), "ng_qty": float(row.ng_qty),
            "wo_status": row.wo_status,
            "start_date": str(row.start_date) if row.start_date else None,
            "finish_date": str(row.finish_date) if row.finish_date else None,
        })


def create_work_order(payload: WorkOrderCreate) -> dict:
    try:
        with session_scope() as session:
            row = repo.create_work_order(session,
                                         wo_no=payload.wo_no,
                                         so_id=payload.so_id,
                                         product_id=payload.product_id,
                                         planned_qty=payload.planned_qty,
                                         wo_status=payload.wo_status)
            return ok({"id": row.id, "wo_no": row.wo_no, "wo_status": row.wo_status}, message="created")
    except IntegrityError as exc:
        raise integrity_http_error(exc) from exc


def update_work_order_status(wo_id: str, payload: StatusUpdate) -> dict:
    with session_scope() as session:
        row = repo.get_work_order(session, wo_id)
        if not row:
            raise not_found_error("work order")
        row.wo_status = payload.status
        return ok({"id": row.id, "wo_no": row.wo_no, "wo_status": row.wo_status}, message="updated")


def update_work_order_qty(wo_id: str, payload: WorkOrderQtyUpdate) -> dict:
    with session_scope() as session:
        row = repo.get_work_order(session, wo_id)
        if not row:
            raise not_found_error("work order")
        row.good_qty = payload.good_qty
        row.ng_qty = payload.ng_qty
        return ok({"id": row.id, "wo_no": row.wo_no,
                   "good_qty": float(row.good_qty), "ng_qty": float(row.ng_qty)}, message="updated")
