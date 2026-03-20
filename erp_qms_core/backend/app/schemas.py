from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class DepartmentCreate(BaseModel):
    dept_code: str
    dept_name: str


class RoleCreate(BaseModel):
    role_code: str
    role_name: str
    description: str = ""


class CustomerCreate(BaseModel):
    customer_code: str
    customer_name: str
    short_name: str = ""


class SupplierCreate(BaseModel):
    supplier_code: str
    supplier_name: str
    category: str = ""


class ProductCreate(BaseModel):
    product_code: str
    product_name: str
    customer_part_no: str = ""
    internal_part_no: str = ""
    spec_summary: str = ""


class InventoryLocationCreate(BaseModel):
    location_code: str
    location_name: str
    location_type: str = "warehouse"
    is_hold_area: bool = False


class SalesOrderCreate(BaseModel):
    so_no: str
    customer_id: str | None = None
    order_date: date | None = None
    due_date: date | None = None
    order_status: str = "draft"
    special_requirement: str = ""


class WorkOrderCreate(BaseModel):
    wo_no: str
    so_id: str | None = None
    product_id: str | None = None
    planned_qty: float = 0
    wo_status: str = "draft"
