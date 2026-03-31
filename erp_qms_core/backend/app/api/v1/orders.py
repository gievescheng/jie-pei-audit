from __future__ import annotations

from fastapi import APIRouter

from ...schemas.common import StatusUpdate, WorkOrderQtyUpdate
from ...schemas.orders import SalesOrderCreate, SalesOrderItemCreate, WorkOrderCreate
from ...services import sales_orders as so_svc
from ...services import work_orders as wo_svc

router = APIRouter()


@router.get("/orders/sales-orders")
def list_sales_orders():
    return so_svc.list_sales_orders()


@router.post("/orders/sales-orders", status_code=201)
def create_sales_order(payload: SalesOrderCreate):
    return so_svc.create_sales_order(payload)


@router.get("/orders/sales-orders/{so_id}")
def get_sales_order(so_id: str):
    return so_svc.get_sales_order(so_id)


@router.put("/orders/sales-orders/{so_id}/status")
def update_sales_order_status(so_id: str, payload: StatusUpdate):
    return so_svc.update_sales_order_status(so_id, payload)


@router.post("/orders/sales-orders/{so_id}/items", status_code=201)
def add_sales_order_item(so_id: str, payload: SalesOrderItemCreate):
    return so_svc.add_sales_order_item(so_id, payload)


@router.get("/orders/work-orders")
def list_work_orders():
    return wo_svc.list_work_orders()


@router.post("/orders/work-orders", status_code=201)
def create_work_order(payload: WorkOrderCreate):
    return wo_svc.create_work_order(payload)


@router.get("/orders/work-orders/{wo_id}")
def get_work_order(wo_id: str):
    return wo_svc.get_work_order(wo_id)


@router.put("/orders/work-orders/{wo_id}/status")
def update_work_order_status(wo_id: str, payload: StatusUpdate):
    return wo_svc.update_work_order_status(wo_id, payload)


@router.put("/orders/work-orders/{wo_id}/qty")
def update_work_order_qty(wo_id: str, payload: WorkOrderQtyUpdate):
    return wo_svc.update_work_order_qty(wo_id, payload)
