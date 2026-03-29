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


# ── 更新格式（所有欄位選填，只傳要改的）────────────────────

class DepartmentUpdate(BaseModel):
    dept_code: str | None = None
    dept_name: str | None = None
    is_active: bool | None = None


class RoleUpdate(BaseModel):
    role_code: str | None = None
    role_name: str | None = None
    description: str | None = None


class CustomerUpdate(BaseModel):
    customer_code: str | None = None
    customer_name: str | None = None
    short_name: str | None = None
    status: str | None = None


class SupplierUpdate(BaseModel):
    supplier_code: str | None = None
    supplier_name: str | None = None
    category: str | None = None
    status: str | None = None


class ProductUpdate(BaseModel):
    product_code: str | None = None
    product_name: str | None = None
    customer_part_no: str | None = None
    internal_part_no: str | None = None
    spec_summary: str | None = None
    status: str | None = None


class InventoryLocationUpdate(BaseModel):
    location_code: str | None = None
    location_name: str | None = None
    location_type: str | None = None
    is_hold_area: bool | None = None


class SalesOrderUpdate(BaseModel):
    customer_id: str | None = None
    order_date: date | None = None
    due_date: date | None = None
    order_status: str | None = None
    special_requirement: str | None = None


class WorkOrderUpdate(BaseModel):
    so_id: str | None = None
    product_id: str | None = None
    planned_qty: float | None = None
    released_qty: float | None = None
    good_qty: float | None = None
    ng_qty: float | None = None
    wo_status: str | None = None
    start_date: date | None = None
    finish_date: date | None = None


# ── 庫存交易 ──────────────────────────────────────────────

class InventoryTransactionCreate(BaseModel):
    """新增庫存交易。trx_no 留空則後端自動產生（TRX-YYYYMMDD-XXXXX）。"""
    trx_no: str | None = None
    trx_type: str                          # IN / OUT / SCRAP / QC / MOVE
    item_type: str                         # "product" / "material" / "work_order"
    item_ref_id: str = ""
    lot_no: str = ""
    qty: float                             # IN=正數，OUT/SCRAP=負數
    location_code: str = ""
    inventory_status: str = "available"    # available / hold / blocked
    trx_date: date | None = None


# ── 登入與通行證相關 ──────────────────────────────────────

class LoginRequest(BaseModel):
    """登入請求：員工編號 + 密碼"""
    emp_no: str
    password: str


class TokenResponse(BaseModel):
    """登入成功後回傳的通行證資訊"""
    access_token: str       # 短效通行證（30 分鐘）
    refresh_token: str      # 長效更新通行證（7 天）
    token_type: str = "bearer"
    user_id: str
    emp_no: str
    name: str
    role_id: str | None = None


class RefreshRequest(BaseModel):
    """更新通行證請求"""
    refresh_token: str


class UserCreate(BaseModel):
    """新增使用者"""
    emp_no: str
    name: str
    email: str | None = None
    password: str
    role_id: str | None = None
    dept_id: str | None = None


class UserUpdate(BaseModel):
    """修改使用者（密碼以外的欄位）"""
    name: str | None = None
    email: str | None = None
    role_id: str | None = None
    dept_id: str | None = None
    is_active: bool | None = None


class UserPasswordReset(BaseModel):
    """重設使用者密碼"""
    new_password: str
