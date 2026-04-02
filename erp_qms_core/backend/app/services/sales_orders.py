from __future__ import annotations

from sqlalchemy.exc import IntegrityError

from fastapi import HTTPException

from ..core.db import session_scope
from ..core.errors import integrity_http_error, not_found_error
from ..domain.transitions import can_transition
from ..core.responses import ok
from ..repositories import orders as repo
from ..schemas.common import StatusUpdate
from ..schemas.orders import SalesOrderCreate, SalesOrderItemCreate


def list_sales_orders() -> dict:
    with session_scope() as session:
        rows = repo.list_sales_orders(session)
        return ok([
            {"id": r.id, "so_no": r.so_no, "customer_id": r.customer_id,
             "order_date": str(r.order_date) if r.order_date else None,
             "due_date": str(r.due_date) if r.due_date else None,
             "order_status": r.order_status}
            for r in rows
        ])


def get_sales_order(so_id: str) -> dict:
    with session_scope() as session:
        row = repo.get_sales_order(session, so_id)
        if not row:
            raise not_found_error("sales order")
        items = repo.list_so_items(session, so_id)
        return ok({
            "id": row.id, "so_no": row.so_no, "customer_id": row.customer_id,
            "order_date": str(row.order_date) if row.order_date else None,
            "due_date": str(row.due_date) if row.due_date else None,
            "order_status": row.order_status, "special_requirement": row.special_requirement,
            "items": [{"id": i.id, "product_id": i.product_id,
                       "ordered_qty": float(i.ordered_qty), "unit": i.unit, "remark": i.remark}
                      for i in items],
        })


def create_sales_order(payload: SalesOrderCreate) -> dict:
    try:
        with session_scope() as session:
            row = repo.create_sales_order(session,
                                          so_no=payload.so_no,
                                          customer_id=payload.customer_id,
                                          order_date=payload.order_date,
                                          due_date=payload.due_date,
                                          order_status=payload.order_status,
                                          special_requirement=payload.special_requirement)
            return ok({"id": row.id, "so_no": row.so_no, "order_status": row.order_status}, message="created")
    except IntegrityError as exc:
        raise integrity_http_error(exc) from exc


def update_sales_order_status(so_id: str, payload: StatusUpdate) -> dict:
    with session_scope() as session:
        row = repo.get_sales_order(session, so_id)
        if not row:
            raise not_found_error("sales order")
        if not can_transition("sales_order", row.order_status, payload.status):
            raise HTTPException(
                status_code=422,
                detail=f"無法從 '{row.order_status}' 轉換為 '{payload.status}'。請確認訂單目前狀態允許此操作。",
            )
        row.order_status = payload.status
        return ok({"id": row.id, "so_no": row.so_no, "order_status": row.order_status}, message="updated")


def add_sales_order_item(so_id: str, payload: SalesOrderItemCreate) -> dict:
    try:
        with session_scope() as session:
            if not repo.get_sales_order(session, so_id):
                raise not_found_error("sales order")
            row = repo.create_so_item(session, so_id,
                                      product_id=payload.product_id,
                                      ordered_qty=payload.ordered_qty,
                                      unit=payload.unit,
                                      remark=payload.remark)
            return ok({"id": row.id, "so_id": row.so_id,
                       "product_id": row.product_id, "ordered_qty": float(row.ordered_qty)}, message="created")
    except IntegrityError as exc:
        raise integrity_http_error(exc) from exc
