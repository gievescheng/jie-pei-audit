from __future__ import annotations

from datetime import date

from pydantic import BaseModel


# ── 主資料：部門 / 角色 ──────────────────────────────────────

class DepartmentCreate(BaseModel):
    dept_code: str
    dept_name: str


class RoleCreate(BaseModel):
    role_code: str
    role_name: str
    description: str = ""


# ── 主資料：客戶 ─────────────────────────────────────────────

class CustomerCreate(BaseModel):
    customer_code: str
    customer_name: str
    short_name: str = ""


class CustomerUpdate(BaseModel):
    customer_name: str | None = None
    short_name: str | None = None
    status: str | None = None


# ── 主資料：供應商 ───────────────────────────────────────────

class SupplierCreate(BaseModel):
    supplier_code: str
    supplier_name: str
    category: str = ""


class SupplierUpdate(BaseModel):
    supplier_name: str | None = None
    category: str | None = None
    status: str | None = None


# ── 主資料：產品 ─────────────────────────────────────────────

class ProductCreate(BaseModel):
    product_code: str
    product_name: str
    customer_part_no: str = ""
    internal_part_no: str = ""
    spec_summary: str = ""


class ProductUpdate(BaseModel):
    product_name: str | None = None
    customer_part_no: str | None = None
    internal_part_no: str | None = None
    spec_summary: str | None = None
    status: str | None = None


# ── 主資料：材料主檔 ─────────────────────────────────────────

class MaterialMasterCreate(BaseModel):
    material_code: str
    material_name: str
    material_type: str = "raw"
    unit: str = "PCS"


class MaterialMasterUpdate(BaseModel):
    material_name: str | None = None
    material_type: str | None = None
    unit: str | None = None
    status: str | None = None


# ── 主資料：BOM ──────────────────────────────────────────────

class BomItemCreate(BaseModel):
    material_id: str
    qty_per: float = 1.0
    loss_rate: float = 0.0


# ── 主資料：班次 ─────────────────────────────────────────────

class ShiftMasterCreate(BaseModel):
    shift_code: str
    shift_name: str
    start_time: str = "08:00"
    end_time: str = "17:00"


# ── 庫存：儲位 ───────────────────────────────────────────────

class InventoryLocationCreate(BaseModel):
    location_code: str
    location_name: str
    location_type: str = "warehouse"
    is_hold_area: bool = False


# ── 庫存：異動 ───────────────────────────────────────────────

class InventoryTransactionCreate(BaseModel):
    trx_no: str
    trx_type: str
    item_type: str
    item_ref_id: str = ""
    lot_no: str = ""
    qty: float = 0
    location_code: str = ""
    inventory_status: str = "available"
    trx_date: date | None = None


# ── 訂單：銷售訂單 ───────────────────────────────────────────

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


# ── 訂單：工單 ───────────────────────────────────────────────

class WorkOrderCreate(BaseModel):
    wo_no: str
    so_id: str | None = None
    product_id: str | None = None
    planned_qty: float = 0
    wo_status: str = "draft"


class WorkOrderQtyUpdate(BaseModel):
    good_qty: float = 0
    ng_qty: float = 0


# ── 出貨 ─────────────────────────────────────────────────────

class ShipmentCreate(BaseModel):
    shipment_no: str
    so_id: str | None = None
    shipment_date: date | None = None
    ship_status: str = "draft"
    remark: str = ""


# ── 通用：狀態更新 ───────────────────────────────────────────

class StatusUpdate(BaseModel):
    status: str
