from __future__ import annotations

from sqlalchemy.orm import Session

from ..models.orders import SalesOrder, SalesOrderItem, WorkOrder


# ── Sales Orders ─────────────────────────────────────────────

def list_sales_orders(session: Session) -> list[SalesOrder]:
    return (
        session.query(SalesOrder)
        .filter(SalesOrder.is_deleted == False)  # noqa: E712
        .order_by(SalesOrder.so_no.asc())
        .all()
    )


def get_sales_order(session: Session, so_id: str) -> SalesOrder | None:
    return (
        session.query(SalesOrder)
        .filter(SalesOrder.id == so_id, SalesOrder.is_deleted == False)  # noqa: E712
        .first()
    )


def create_sales_order(session: Session, **kwargs) -> SalesOrder:
    row = SalesOrder(**kwargs)
    session.add(row)
    session.flush()
    return row


def list_so_items(session: Session, so_id: str) -> list[SalesOrderItem]:
    return (
        session.query(SalesOrderItem)
        .filter(SalesOrderItem.so_id == so_id, SalesOrderItem.is_deleted == False)  # noqa: E712
        .all()
    )


def create_so_item(session: Session, so_id: str, **kwargs) -> SalesOrderItem:
    row = SalesOrderItem(so_id=so_id, **kwargs)
    session.add(row)
    session.flush()
    return row


# ── Work Orders ──────────────────────────────────────────────

def list_work_orders(session: Session) -> list[WorkOrder]:
    return (
        session.query(WorkOrder)
        .filter(WorkOrder.is_deleted == False)  # noqa: E712
        .order_by(WorkOrder.wo_no.asc())
        .all()
    )


def get_work_order(session: Session, wo_id: str) -> WorkOrder | None:
    return (
        session.query(WorkOrder)
        .filter(WorkOrder.id == wo_id, WorkOrder.is_deleted == False)  # noqa: E712
        .first()
    )


def create_work_order(session: Session, **kwargs) -> WorkOrder:
    row = WorkOrder(**kwargs)
    session.add(row)
    session.flush()
    return row
