from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class SalesOrderCreate(BaseModel):
    so_no: str
    customer_id: str | None = None
    order_date: date | None = None
    due_date: date | None = None
    order_status: str = "draft"
    special_requirement: str = ""


class SalesOrderItemCreate(BaseModel):
    product_id: str | None = None
    ordered_qty: float = 0
    unit: str = "PCS"
    remark: str = ""


class WorkOrderCreate(BaseModel):
    wo_no: str
    so_id: str | None = None
    product_id: str | None = None
    planned_qty: float = 0
    wo_status: str = "draft"
