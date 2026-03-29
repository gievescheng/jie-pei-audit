from __future__ import annotations

import hashlib
import uuid
import datetime as _dt
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query, Request
from sqlalchemy.exc import IntegrityError

from . import auth, models, schemas
from .db import session_scope


router = APIRouter(prefix="/api", tags=["erp-qms-core"])


def ok(data, message="OK"):
    return {
        "success": True,
        "data": data,
        "message": message,
        "trace_id": str(uuid.uuid4()),
    }


def _integrity_http_error(exc: IntegrityError) -> HTTPException:
    detail = str(getattr(exc, "orig", exc)).lower()
    if "unique constraint" in detail or "duplicate key value" in detail:
        return HTTPException(status_code=409, detail="resource already exists")
    if "foreign key constraint" in detail or "violates foreign key constraint" in detail:
        return HTTPException(status_code=422, detail="related resource does not exist")
    return HTTPException(status_code=400, detail="invalid database write")


@router.get("/health")
def health():
    return ok({"service": "jepe-erp-qms-core"}, message="healthy")


@router.get("/master/departments")
def list_departments(request: Request, q: str = Query(default="", description="關鍵字搜尋"), limit: int = Query(default=50, ge=1, le=200), offset: int = Query(default=0, ge=0)):
    auth.require_permission(auth.extract_bearer(request.headers.get("Authorization")), "master.department.read")
    with session_scope() as session:
        query = session.query(models.Department).filter(models.Department.is_deleted == False)
        if q:
            query = query.filter(models.Department.dept_name.contains(q) | models.Department.dept_code.contains(q))
        total = query.count()
        rows = query.order_by(models.Department.dept_code.asc()).offset(offset).limit(limit).all()
        return ok({"total": total, "items": [{"id": r.id, "dept_code": r.dept_code, "dept_name": r.dept_name, "is_active": r.is_active} for r in rows]})


@router.post("/master/departments")
def create_department(request: Request, payload: schemas.DepartmentCreate):
    auth.require_permission(auth.extract_bearer(request.headers.get("Authorization")), "master.department.write")
    try:
        with session_scope() as session:
            row = models.Department(dept_code=payload.dept_code, dept_name=payload.dept_name)
            session.add(row)
            session.flush()
            return ok({"id": row.id, "dept_code": row.dept_code, "dept_name": row.dept_name}, message="created")
    except IntegrityError as exc:
        raise _integrity_http_error(exc) from exc


@router.get("/master/departments/{dept_id}")
def get_department(request: Request, dept_id: str):
    auth.require_permission(auth.extract_bearer(request.headers.get("Authorization")), "master.department.read")
    with session_scope() as session:
        row = session.query(models.Department).filter(models.Department.id == dept_id, models.Department.is_deleted == False).first()
        if row is None:
            raise HTTPException(status_code=404, detail="找不到此部門")
        return ok({"id": row.id, "dept_code": row.dept_code, "dept_name": row.dept_name, "is_active": row.is_active})


@router.patch("/master/departments/{dept_id}")
def update_department(request: Request, dept_id: str, payload: schemas.DepartmentUpdate):
    auth.require_permission(auth.extract_bearer(request.headers.get("Authorization")), "master.department.write")
    try:
        with session_scope() as session:
            row = session.query(models.Department).filter(models.Department.id == dept_id, models.Department.is_deleted == False).first()
            if row is None:
                raise HTTPException(status_code=404, detail="找不到此部門")
            for field, value in payload.model_dump(exclude_none=True).items():
                setattr(row, field, value)
            session.flush()
            return ok({"id": row.id, "dept_code": row.dept_code, "dept_name": row.dept_name}, message="updated")
    except IntegrityError as exc:
        raise _integrity_http_error(exc) from exc


@router.delete("/master/departments/{dept_id}")
def delete_department(request: Request, dept_id: str):
    auth.require_permission(auth.extract_bearer(request.headers.get("Authorization")), "master.department.write")
    with session_scope() as session:
        row = session.query(models.Department).filter(models.Department.id == dept_id, models.Department.is_deleted == False).first()
        if row is None:
            raise HTTPException(status_code=404, detail="找不到此部門")
        row.is_deleted = True
        return ok({}, message="deleted")


@router.get("/master/roles")
def list_roles(request: Request, q: str = Query(default="", description="關鍵字搜尋"), limit: int = Query(default=50, ge=1, le=200), offset: int = Query(default=0, ge=0)):
    auth.require_permission(auth.extract_bearer(request.headers.get("Authorization")), "master.role.read")
    with session_scope() as session:
        query = session.query(models.Role).filter(models.Role.is_deleted == False)
        if q:
            query = query.filter(models.Role.role_name.contains(q) | models.Role.role_code.contains(q))
        total = query.count()
        rows = query.order_by(models.Role.role_code.asc()).offset(offset).limit(limit).all()
        return ok({"total": total, "items": [{"id": r.id, "role_code": r.role_code, "role_name": r.role_name, "description": r.description} for r in rows]})


@router.post("/master/roles")
def create_role(request: Request, payload: schemas.RoleCreate):
    auth.require_permission(auth.extract_bearer(request.headers.get("Authorization")), "master.role.write")
    try:
        with session_scope() as session:
            row = models.Role(role_code=payload.role_code, role_name=payload.role_name, description=payload.description)
            session.add(row)
            session.flush()
            return ok({"id": row.id, "role_code": row.role_code, "role_name": row.role_name}, message="created")
    except IntegrityError as exc:
        raise _integrity_http_error(exc) from exc


@router.get("/master/roles/{role_id}")
def get_role(request: Request, role_id: str):
    auth.require_permission(auth.extract_bearer(request.headers.get("Authorization")), "master.role.read")
    with session_scope() as session:
        row = session.query(models.Role).filter(models.Role.id == role_id, models.Role.is_deleted == False).first()
        if row is None:
            raise HTTPException(status_code=404, detail="找不到此角色")
        return ok({"id": row.id, "role_code": row.role_code, "role_name": row.role_name, "description": row.description})


@router.patch("/master/roles/{role_id}")
def update_role(request: Request, role_id: str, payload: schemas.RoleUpdate):
    auth.require_permission(auth.extract_bearer(request.headers.get("Authorization")), "master.role.write")
    try:
        with session_scope() as session:
            row = session.query(models.Role).filter(models.Role.id == role_id, models.Role.is_deleted == False).first()
            if row is None:
                raise HTTPException(status_code=404, detail="找不到此角色")
            for field, value in payload.model_dump(exclude_none=True).items():
                setattr(row, field, value)
            session.flush()
            return ok({"id": row.id, "role_code": row.role_code, "role_name": row.role_name}, message="updated")
    except IntegrityError as exc:
        raise _integrity_http_error(exc) from exc


@router.delete("/master/roles/{role_id}")
def delete_role(request: Request, role_id: str):
    auth.require_permission(auth.extract_bearer(request.headers.get("Authorization")), "master.role.write")
    with session_scope() as session:
        row = session.query(models.Role).filter(models.Role.id == role_id, models.Role.is_deleted == False).first()
        if row is None:
            raise HTTPException(status_code=404, detail="找不到此角色")
        row.is_deleted = True
        return ok({}, message="deleted")


@router.get("/master/customers")
def list_customers(request: Request, q: str = Query(default="", description="關鍵字搜尋"), limit: int = Query(default=50, ge=1, le=200), offset: int = Query(default=0, ge=0)):
    auth.require_permission(auth.extract_bearer(request.headers.get("Authorization")), "master.customer.read")
    with session_scope() as session:
        query = session.query(models.Customer).filter(models.Customer.is_deleted == False)
        if q:
            query = query.filter(models.Customer.customer_name.contains(q) | models.Customer.customer_code.contains(q))
        total = query.count()
        rows = query.order_by(models.Customer.customer_code.asc()).offset(offset).limit(limit).all()
        return ok({"total": total, "items": [{"id": r.id, "customer_code": r.customer_code, "customer_name": r.customer_name, "short_name": r.short_name, "status": r.status} for r in rows]})


@router.post("/master/customers")
def create_customer(request: Request, payload: schemas.CustomerCreate):
    auth.require_permission(auth.extract_bearer(request.headers.get("Authorization")), "master.customer.write")
    try:
        with session_scope() as session:
            row = models.Customer(customer_code=payload.customer_code, customer_name=payload.customer_name, short_name=payload.short_name)
            session.add(row)
            session.flush()
            return ok({"id": row.id, "customer_code": row.customer_code, "customer_name": row.customer_name}, message="created")
    except IntegrityError as exc:
        raise _integrity_http_error(exc) from exc


@router.get("/master/customers/{customer_id}")
def get_customer(request: Request, customer_id: str):
    auth.require_permission(auth.extract_bearer(request.headers.get("Authorization")), "master.customer.read")
    with session_scope() as session:
        row = session.query(models.Customer).filter(models.Customer.id == customer_id, models.Customer.is_deleted == False).first()
        if row is None:
            raise HTTPException(status_code=404, detail="找不到此客戶")
        return ok({"id": row.id, "customer_code": row.customer_code, "customer_name": row.customer_name, "short_name": row.short_name, "status": row.status})


@router.patch("/master/customers/{customer_id}")
def update_customer(request: Request, customer_id: str, payload: schemas.CustomerUpdate):
    auth.require_permission(auth.extract_bearer(request.headers.get("Authorization")), "master.customer.write")
    try:
        with session_scope() as session:
            row = session.query(models.Customer).filter(models.Customer.id == customer_id, models.Customer.is_deleted == False).first()
            if row is None:
                raise HTTPException(status_code=404, detail="找不到此客戶")
            for field, value in payload.model_dump(exclude_none=True).items():
                setattr(row, field, value)
            session.flush()
            return ok({"id": row.id, "customer_code": row.customer_code, "customer_name": row.customer_name}, message="updated")
    except IntegrityError as exc:
        raise _integrity_http_error(exc) from exc


@router.delete("/master/customers/{customer_id}")
def delete_customer(request: Request, customer_id: str):
    auth.require_permission(auth.extract_bearer(request.headers.get("Authorization")), "master.customer.write")
    with session_scope() as session:
        row = session.query(models.Customer).filter(models.Customer.id == customer_id, models.Customer.is_deleted == False).first()
        if row is None:
            raise HTTPException(status_code=404, detail="找不到此客戶")
        row.is_deleted = True
        return ok({}, message="deleted")


@router.get("/master/suppliers")
def list_suppliers(request: Request, q: str = Query(default="", description="關鍵字搜尋"), limit: int = Query(default=50, ge=1, le=200), offset: int = Query(default=0, ge=0)):
    auth.require_permission(auth.extract_bearer(request.headers.get("Authorization")), "master.supplier.read")
    with session_scope() as session:
        query = session.query(models.Supplier).filter(models.Supplier.is_deleted == False)
        if q:
            query = query.filter(models.Supplier.supplier_name.contains(q) | models.Supplier.supplier_code.contains(q))
        total = query.count()
        rows = query.order_by(models.Supplier.supplier_code.asc()).offset(offset).limit(limit).all()
        return ok({"total": total, "items": [{"id": r.id, "supplier_code": r.supplier_code, "supplier_name": r.supplier_name, "category": r.category, "status": r.status} for r in rows]})


@router.post("/master/suppliers")
def create_supplier(request: Request, payload: schemas.SupplierCreate):
    auth.require_permission(auth.extract_bearer(request.headers.get("Authorization")), "master.supplier.write")
    try:
        with session_scope() as session:
            row = models.Supplier(supplier_code=payload.supplier_code, supplier_name=payload.supplier_name, category=payload.category)
            session.add(row)
            session.flush()
            return ok({"id": row.id, "supplier_code": row.supplier_code, "supplier_name": row.supplier_name}, message="created")
    except IntegrityError as exc:
        raise _integrity_http_error(exc) from exc


@router.get("/master/suppliers/{supplier_id}")
def get_supplier(request: Request, supplier_id: str):
    auth.require_permission(auth.extract_bearer(request.headers.get("Authorization")), "master.supplier.read")
    with session_scope() as session:
        row = session.query(models.Supplier).filter(models.Supplier.id == supplier_id, models.Supplier.is_deleted == False).first()
        if row is None:
            raise HTTPException(status_code=404, detail="找不到此供應商")
        return ok({"id": row.id, "supplier_code": row.supplier_code, "supplier_name": row.supplier_name, "category": row.category, "status": row.status})


@router.patch("/master/suppliers/{supplier_id}")
def update_supplier(request: Request, supplier_id: str, payload: schemas.SupplierUpdate):
    auth.require_permission(auth.extract_bearer(request.headers.get("Authorization")), "master.supplier.write")
    try:
        with session_scope() as session:
            row = session.query(models.Supplier).filter(models.Supplier.id == supplier_id, models.Supplier.is_deleted == False).first()
            if row is None:
                raise HTTPException(status_code=404, detail="找不到此供應商")
            for field, value in payload.model_dump(exclude_none=True).items():
                setattr(row, field, value)
            session.flush()
            return ok({"id": row.id, "supplier_code": row.supplier_code, "supplier_name": row.supplier_name}, message="updated")
    except IntegrityError as exc:
        raise _integrity_http_error(exc) from exc


@router.delete("/master/suppliers/{supplier_id}")
def delete_supplier(request: Request, supplier_id: str):
    auth.require_permission(auth.extract_bearer(request.headers.get("Authorization")), "master.supplier.write")
    with session_scope() as session:
        row = session.query(models.Supplier).filter(models.Supplier.id == supplier_id, models.Supplier.is_deleted == False).first()
        if row is None:
            raise HTTPException(status_code=404, detail="找不到此供應商")
        row.is_deleted = True
        return ok({}, message="deleted")


@router.get("/master/products")
def list_products(request: Request, q: str = Query(default="", description="關鍵字搜尋"), limit: int = Query(default=50, ge=1, le=200), offset: int = Query(default=0, ge=0)):
    auth.require_permission(auth.extract_bearer(request.headers.get("Authorization")), "master.product.read")
    with session_scope() as session:
        query = session.query(models.Product).filter(models.Product.is_deleted == False)
        if q:
            query = query.filter(models.Product.product_name.contains(q) | models.Product.product_code.contains(q))
        total = query.count()
        rows = query.order_by(models.Product.product_code.asc()).offset(offset).limit(limit).all()
        return ok({"total": total, "items": [{"id": r.id, "product_code": r.product_code, "product_name": r.product_name, "status": r.status} for r in rows]})


@router.post("/master/products")
def create_product(request: Request, payload: schemas.ProductCreate):
    auth.require_permission(auth.extract_bearer(request.headers.get("Authorization")), "master.product.write")
    try:
        with session_scope() as session:
            row = models.Product(
                product_code=payload.product_code,
                product_name=payload.product_name,
                customer_part_no=payload.customer_part_no,
                internal_part_no=payload.internal_part_no,
                spec_summary=payload.spec_summary,
            )
            session.add(row)
            session.flush()
            return ok({"id": row.id, "product_code": row.product_code, "product_name": row.product_name}, message="created")
    except IntegrityError as exc:
        raise _integrity_http_error(exc) from exc


@router.get("/master/products/{product_id}")
def get_product(request: Request, product_id: str):
    auth.require_permission(auth.extract_bearer(request.headers.get("Authorization")), "master.product.read")
    with session_scope() as session:
        row = session.query(models.Product).filter(models.Product.id == product_id, models.Product.is_deleted == False).first()
        if row is None:
            raise HTTPException(status_code=404, detail="找不到此產品")
        return ok({"id": row.id, "product_code": row.product_code, "product_name": row.product_name, "customer_part_no": row.customer_part_no, "internal_part_no": row.internal_part_no, "spec_summary": row.spec_summary, "status": row.status})


@router.patch("/master/products/{product_id}")
def update_product(request: Request, product_id: str, payload: schemas.ProductUpdate):
    auth.require_permission(auth.extract_bearer(request.headers.get("Authorization")), "master.product.write")
    try:
        with session_scope() as session:
            row = session.query(models.Product).filter(models.Product.id == product_id, models.Product.is_deleted == False).first()
            if row is None:
                raise HTTPException(status_code=404, detail="找不到此產品")
            for field, value in payload.model_dump(exclude_none=True).items():
                setattr(row, field, value)
            session.flush()
            return ok({"id": row.id, "product_code": row.product_code, "product_name": row.product_name}, message="updated")
    except IntegrityError as exc:
        raise _integrity_http_error(exc) from exc


@router.delete("/master/products/{product_id}")
def delete_product(request: Request, product_id: str):
    auth.require_permission(auth.extract_bearer(request.headers.get("Authorization")), "master.product.write")
    with session_scope() as session:
        row = session.query(models.Product).filter(models.Product.id == product_id, models.Product.is_deleted == False).first()
        if row is None:
            raise HTTPException(status_code=404, detail="找不到此產品")
        row.is_deleted = True
        return ok({}, message="deleted")


@router.get("/inventory/locations")
def list_locations(request: Request, q: str = Query(default="", description="關鍵字搜尋"), limit: int = Query(default=50, ge=1, le=200), offset: int = Query(default=0, ge=0)):
    auth.require_permission(auth.extract_bearer(request.headers.get("Authorization")), "inventory.location.read")
    with session_scope() as session:
        query = session.query(models.InventoryLocation).filter(models.InventoryLocation.is_deleted == False)
        if q:
            query = query.filter(models.InventoryLocation.location_name.contains(q) | models.InventoryLocation.location_code.contains(q))
        total = query.count()
        rows = query.order_by(models.InventoryLocation.location_code.asc()).offset(offset).limit(limit).all()
        return ok({"total": total, "items": [{"id": r.id, "location_code": r.location_code, "location_name": r.location_name, "location_type": r.location_type, "is_hold_area": r.is_hold_area} for r in rows]})


@router.post("/inventory/locations")
def create_location(request: Request, payload: schemas.InventoryLocationCreate):
    auth.require_permission(auth.extract_bearer(request.headers.get("Authorization")), "inventory.location.write")
    try:
        with session_scope() as session:
            row = models.InventoryLocation(
                location_code=payload.location_code,
                location_name=payload.location_name,
                location_type=payload.location_type,
                is_hold_area=payload.is_hold_area,
            )
            session.add(row)
            session.flush()
            return ok({"id": row.id, "location_code": row.location_code, "location_name": row.location_name}, message="created")
    except IntegrityError as exc:
        raise _integrity_http_error(exc) from exc


@router.get("/inventory/locations/{location_id}")
def get_location(request: Request, location_id: str):
    auth.require_permission(auth.extract_bearer(request.headers.get("Authorization")), "inventory.location.read")
    with session_scope() as session:
        row = session.query(models.InventoryLocation).filter(models.InventoryLocation.id == location_id, models.InventoryLocation.is_deleted == False).first()
        if row is None:
            raise HTTPException(status_code=404, detail="找不到此庫存位置")
        return ok({"id": row.id, "location_code": row.location_code, "location_name": row.location_name, "location_type": row.location_type, "is_hold_area": row.is_hold_area})


@router.patch("/inventory/locations/{location_id}")
def update_location(request: Request, location_id: str, payload: schemas.InventoryLocationUpdate):
    auth.require_permission(auth.extract_bearer(request.headers.get("Authorization")), "inventory.location.write")
    try:
        with session_scope() as session:
            row = session.query(models.InventoryLocation).filter(models.InventoryLocation.id == location_id, models.InventoryLocation.is_deleted == False).first()
            if row is None:
                raise HTTPException(status_code=404, detail="找不到此庫存位置")
            for field, value in payload.model_dump(exclude_none=True).items():
                setattr(row, field, value)
            session.flush()
            return ok({"id": row.id, "location_code": row.location_code, "location_name": row.location_name}, message="updated")
    except IntegrityError as exc:
        raise _integrity_http_error(exc) from exc


@router.delete("/inventory/locations/{location_id}")
def delete_location(request: Request, location_id: str):
    auth.require_permission(auth.extract_bearer(request.headers.get("Authorization")), "inventory.location.write")
    with session_scope() as session:
        row = session.query(models.InventoryLocation).filter(models.InventoryLocation.id == location_id, models.InventoryLocation.is_deleted == False).first()
        if row is None:
            raise HTTPException(status_code=404, detail="找不到此庫存位置")
        row.is_deleted = True
        return ok({}, message="deleted")


# ─── 庫存交易 Endpoints ───────────────────────────────────────────────────────

@router.get("/inventory/transactions")
def list_transactions(
    request: Request,
    location_code: str = Query(default=""),
    item_type: str = Query(default=""),
    inventory_status: str = Query(default=""),
    trx_type: str = Query(default=""),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    """列出庫存交易記錄，支援多條件篩選。"""
    auth.require_permission(auth.extract_bearer(request.headers.get("Authorization")), "inventory.location.read")
    with session_scope() as session:
        query = session.query(models.InventoryTransaction).filter(models.InventoryTransaction.is_deleted == False)
        if location_code:
            query = query.filter(models.InventoryTransaction.location_code == location_code)
        if item_type:
            query = query.filter(models.InventoryTransaction.item_type == item_type)
        if inventory_status:
            query = query.filter(models.InventoryTransaction.inventory_status == inventory_status)
        if trx_type:
            query = query.filter(models.InventoryTransaction.trx_type == trx_type)
        total = query.count()
        rows = (
            query.order_by(models.InventoryTransaction.trx_date.desc(), models.InventoryTransaction.created_at.desc())
            .offset(offset).limit(limit).all()
        )
        items = [
            {
                "id": r.id,
                "trx_no": r.trx_no,
                "trx_type": r.trx_type,
                "item_type": r.item_type,
                "item_ref_id": r.item_ref_id,
                "lot_no": r.lot_no,
                "qty": float(r.qty),
                "location_code": r.location_code,
                "inventory_status": r.inventory_status,
                "trx_date": str(r.trx_date) if r.trx_date else None,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "created_by": r.created_by,
            }
            for r in rows
        ]
        return ok({"total": total, "items": items})


@router.post("/inventory/transactions")
def create_transaction(request: Request, payload: schemas.InventoryTransactionCreate):
    """新增一筆庫存交易記錄。"""
    user = auth.require_permission(auth.extract_bearer(request.headers.get("Authorization")), "inventory.location.write")
    try:
        with session_scope() as session:
            if payload.trx_no:
                trx_no = payload.trx_no
            else:
                today = _dt.date.today().strftime("%Y%m%d")
                suffix = str(uuid.uuid4())[:8].upper()
                trx_no = f"TRX-{today}-{suffix}"
            trx_date = payload.trx_date or _dt.date.today()
            row = models.InventoryTransaction(
                trx_no=trx_no,
                trx_type=payload.trx_type,
                item_type=payload.item_type,
                item_ref_id=payload.item_ref_id,
                lot_no=payload.lot_no,
                qty=payload.qty,
                location_code=payload.location_code,
                inventory_status=payload.inventory_status,
                trx_date=trx_date,
                created_by=user.emp_no,
            )
            session.add(row)
            session.flush()
            return ok({"id": row.id, "trx_no": row.trx_no, "trx_type": row.trx_type, "qty": float(row.qty), "trx_date": str(row.trx_date)}, message="created")
    except IntegrityError as exc:
        raise _integrity_http_error(exc) from exc


@router.get("/inventory/balances")
def get_inventory_balances(
    request: Request,
    location_code: str = Query(default=""),
    item_type: str = Query(default=""),
):
    """取得庫存結餘，依 (location_code, item_type, item_ref_id, inventory_status) 彙整。"""
    auth.require_permission(auth.extract_bearer(request.headers.get("Authorization")), "inventory.location.read")
    from sqlalchemy import func
    with session_scope() as session:
        query = session.query(
            models.InventoryTransaction.item_type,
            models.InventoryTransaction.item_ref_id,
            models.InventoryTransaction.location_code,
            models.InventoryTransaction.inventory_status,
            func.sum(models.InventoryTransaction.qty).label("balance"),
        ).filter(models.InventoryTransaction.is_deleted == False)
        if location_code:
            query = query.filter(models.InventoryTransaction.location_code == location_code)
        if item_type:
            query = query.filter(models.InventoryTransaction.item_type == item_type)
        rows = query.group_by(
            models.InventoryTransaction.item_type,
            models.InventoryTransaction.item_ref_id,
            models.InventoryTransaction.location_code,
            models.InventoryTransaction.inventory_status,
        ).all()
        items = [
            {
                "item_type": r.item_type,
                "item_ref_id": r.item_ref_id,
                "location_code": r.location_code,
                "inventory_status": r.inventory_status,
                "balance": float(r.balance or 0),
            }
            for r in rows
        ]
        return ok({"items": items})


@router.get("/orders/sales-orders")
def list_sales_orders(request: Request, q: str = Query(default="", description="關鍵字搜尋"), limit: int = Query(default=50, ge=1, le=200), offset: int = Query(default=0, ge=0)):
    auth.require_permission(auth.extract_bearer(request.headers.get("Authorization")), "order.sales.read")
    with session_scope() as session:
        query = session.query(models.SalesOrder).filter(models.SalesOrder.is_deleted == False)
        if q:
            query = query.filter(models.SalesOrder.so_no.contains(q))
        total = query.count()
        rows = query.order_by(models.SalesOrder.so_no.asc()).offset(offset).limit(limit).all()
        return ok({"total": total, "items": [{"id": r.id, "so_no": r.so_no, "order_status": r.order_status, "order_date": str(r.order_date) if r.order_date else None, "due_date": str(r.due_date) if r.due_date else None} for r in rows]})


@router.post("/orders/sales-orders")
def create_sales_order(request: Request, payload: schemas.SalesOrderCreate):
    auth.require_permission(auth.extract_bearer(request.headers.get("Authorization")), "order.sales.write")
    try:
        with session_scope() as session:
            row = models.SalesOrder(
                so_no=payload.so_no,
                customer_id=payload.customer_id,
                order_date=payload.order_date,
                due_date=payload.due_date,
                order_status=payload.order_status,
                special_requirement=payload.special_requirement,
            )
            session.add(row)
            session.flush()
            return ok({"id": row.id, "so_no": row.so_no, "order_status": row.order_status}, message="created")
    except IntegrityError as exc:
        raise _integrity_http_error(exc) from exc


@router.get("/orders/sales-orders/{so_id}")
def get_sales_order(request: Request, so_id: str):
    auth.require_permission(auth.extract_bearer(request.headers.get("Authorization")), "order.sales.read")
    with session_scope() as session:
        row = session.query(models.SalesOrder).filter(models.SalesOrder.id == so_id, models.SalesOrder.is_deleted == False).first()
        if row is None:
            raise HTTPException(status_code=404, detail="找不到此銷售訂單")
        return ok({"id": row.id, "so_no": row.so_no, "customer_id": row.customer_id, "order_status": row.order_status, "order_date": str(row.order_date) if row.order_date else None, "due_date": str(row.due_date) if row.due_date else None, "special_requirement": row.special_requirement})


@router.patch("/orders/sales-orders/{so_id}")
def update_sales_order(request: Request, so_id: str, payload: schemas.SalesOrderUpdate):
    auth.require_permission(auth.extract_bearer(request.headers.get("Authorization")), "order.sales.write")
    try:
        with session_scope() as session:
            row = session.query(models.SalesOrder).filter(models.SalesOrder.id == so_id, models.SalesOrder.is_deleted == False).first()
            if row is None:
                raise HTTPException(status_code=404, detail="找不到此銷售訂單")
            for field, value in payload.model_dump(exclude_none=True).items():
                setattr(row, field, value)
            session.flush()
            return ok({"id": row.id, "so_no": row.so_no, "order_status": row.order_status}, message="updated")
    except IntegrityError as exc:
        raise _integrity_http_error(exc) from exc


@router.delete("/orders/sales-orders/{so_id}")
def delete_sales_order(request: Request, so_id: str):
    auth.require_permission(auth.extract_bearer(request.headers.get("Authorization")), "order.sales.write")
    with session_scope() as session:
        row = session.query(models.SalesOrder).filter(models.SalesOrder.id == so_id, models.SalesOrder.is_deleted == False).first()
        if row is None:
            raise HTTPException(status_code=404, detail="找不到此銷售訂單")
        row.is_deleted = True
        return ok({}, message="deleted")


@router.get("/orders/work-orders")
def list_work_orders(request: Request, q: str = Query(default="", description="關鍵字搜尋"), limit: int = Query(default=50, ge=1, le=200), offset: int = Query(default=0, ge=0)):
    auth.require_permission(auth.extract_bearer(request.headers.get("Authorization")), "order.work.read")
    with session_scope() as session:
        query = session.query(models.WorkOrder).filter(models.WorkOrder.is_deleted == False)
        if q:
            query = query.filter(models.WorkOrder.wo_no.contains(q))
        total = query.count()
        rows = query.order_by(models.WorkOrder.wo_no.asc()).offset(offset).limit(limit).all()
        return ok({"total": total, "items": [{"id": r.id, "wo_no": r.wo_no, "wo_status": r.wo_status, "planned_qty": float(r.planned_qty)} for r in rows]})


@router.post("/orders/work-orders")
def create_work_order(request: Request, payload: schemas.WorkOrderCreate):
    auth.require_permission(auth.extract_bearer(request.headers.get("Authorization")), "order.work.write")
    try:
        with session_scope() as session:
            row = models.WorkOrder(
                wo_no=payload.wo_no,
                so_id=payload.so_id,
                product_id=payload.product_id,
                planned_qty=payload.planned_qty,
                wo_status=payload.wo_status,
            )
            session.add(row)
            session.flush()
            return ok({"id": row.id, "wo_no": row.wo_no, "wo_status": row.wo_status}, message="created")
    except IntegrityError as exc:
        raise _integrity_http_error(exc) from exc


@router.get("/orders/work-orders/{wo_id}")
def get_work_order(request: Request, wo_id: str):
    auth.require_permission(auth.extract_bearer(request.headers.get("Authorization")), "order.work.read")
    with session_scope() as session:
        row = session.query(models.WorkOrder).filter(models.WorkOrder.id == wo_id, models.WorkOrder.is_deleted == False).first()
        if row is None:
            raise HTTPException(status_code=404, detail="找不到此工單")
        return ok({"id": row.id, "wo_no": row.wo_no, "so_id": row.so_id, "product_id": row.product_id, "wo_status": row.wo_status, "planned_qty": float(row.planned_qty), "released_qty": float(row.released_qty), "good_qty": float(row.good_qty), "ng_qty": float(row.ng_qty), "start_date": str(row.start_date) if row.start_date else None, "finish_date": str(row.finish_date) if row.finish_date else None})


@router.patch("/orders/work-orders/{wo_id}")
def update_work_order(request: Request, wo_id: str, payload: schemas.WorkOrderUpdate):
    auth.require_permission(auth.extract_bearer(request.headers.get("Authorization")), "order.work.write")
    try:
        with session_scope() as session:
            row = session.query(models.WorkOrder).filter(models.WorkOrder.id == wo_id, models.WorkOrder.is_deleted == False).first()
            if row is None:
                raise HTTPException(status_code=404, detail="找不到此工單")
            for field, value in payload.model_dump(exclude_none=True).items():
                setattr(row, field, value)
            session.flush()
            return ok({"id": row.id, "wo_no": row.wo_no, "wo_status": row.wo_status}, message="updated")
    except IntegrityError as exc:
        raise _integrity_http_error(exc) from exc


@router.delete("/orders/work-orders/{wo_id}")
def delete_work_order(request: Request, wo_id: str):
    auth.require_permission(auth.extract_bearer(request.headers.get("Authorization")), "order.work.write")
    with session_scope() as session:
        row = session.query(models.WorkOrder).filter(models.WorkOrder.id == wo_id, models.WorkOrder.is_deleted == False).first()
        if row is None:
            raise HTTPException(status_code=404, detail="找不到此工單")
        row.is_deleted = True
        return ok({}, message="deleted")


# ── 登入與權限管理 API ────────────────────────────────────

@router.post("/auth/login")
def login(payload: schemas.LoginRequest):
    """
    登入：輸入員工編號與密碼，回傳通行證。
    通行證分兩種：
    - access_token：短效（30 分鐘），每次 API 呼叫都要帶著
    - refresh_token：長效（7 天），access_token 過期時用來換新的
    """
    with session_scope() as session:
        user = (
            session.query(models.User)
            .filter(
                models.User.emp_no == payload.emp_no,
                models.User.is_active == True,
                models.User.is_deleted == False,
            )
            .first()
        )
        # 無論帳號存不存在都跑一次密碼驗證，防止計時攻擊推測帳號是否存在
        stored_hash = user.password_hash if user else auth._DUMMY_HASH
        valid = auth.verify_password(payload.password, stored_hash)
        if not user or not valid:
            raise HTTPException(status_code=401, detail="帳號或密碼錯誤")

        access_token = auth.create_access_token({
            "sub": user.id,
            "emp_no": user.emp_no,
            "role_id": user.role_id,
        })
        raw_refresh, token_hash = auth.create_refresh_token(user.id)
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        rt = models.RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        session.add(rt)
        session.flush()

        return ok(
            schemas.TokenResponse(
                access_token=access_token,
                refresh_token=raw_refresh,
                user_id=user.id,
                emp_no=user.emp_no,
                name=user.name,
                role_id=user.role_id,
            ).model_dump(),
            message="登入成功",
        )


@router.post("/auth/refresh")
def refresh_token(payload: schemas.RefreshRequest):
    """
    更新通行證：用舊的 refresh_token 換一張新的 access_token + refresh_token。
    舊的 refresh_token 會立即失效（防止被盜用）。
    """
    token_hash = hashlib.sha256(payload.refresh_token.encode()).hexdigest()
    with session_scope() as session:
        rt = (
            session.query(models.RefreshToken)
            .filter(
                models.RefreshToken.token_hash == token_hash,
                models.RefreshToken.revoked == False,
            )
            .first()
        )
        if rt is None or rt.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="更新通行證無效或已過期，請重新登入")

        # 撤銷舊的 refresh token（輪替機制）
        rt.revoked = True
        session.flush()

        user = (
            session.query(models.User)
            .filter(models.User.id == rt.user_id, models.User.is_active == True)
            .first()
        )
        if user is None:
            raise HTTPException(status_code=401, detail="使用者不存在或已停用")

        access_token = auth.create_access_token({
            "sub": user.id,
            "emp_no": user.emp_no,
            "role_id": user.role_id,
        })
        raw_refresh, new_hash = auth.create_refresh_token(user.id)
        new_rt = models.RefreshToken(
            user_id=user.id,
            token_hash=new_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        session.add(new_rt)
        session.flush()

        return ok({
            "access_token": access_token,
            "refresh_token": raw_refresh,
            "token_type": "bearer",
        }, message="通行證已更新")


@router.post("/auth/logout")
def logout(payload: schemas.RefreshRequest):
    """
    登出：撤銷 refresh_token，讓它無法再換新的 access_token。
    注意：access_token 本身會在 30 分鐘後自動過期。
    """
    token_hash = hashlib.sha256(payload.refresh_token.encode()).hexdigest()
    with session_scope() as session:
        rt = (
            session.query(models.RefreshToken)
            .filter(models.RefreshToken.token_hash == token_hash)
            .first()
        )
        if rt:
            rt.revoked = True
    return ok({}, message="已登出")


@router.get("/auth/me")
def get_me(request: Request):
    """
    查詢目前登入的帳號資訊與擁有的權限清單。
    需要在 Header 帶上：Authorization: Bearer <access_token>
    """
    token = auth.extract_bearer(request.headers.get("Authorization"))
    user = auth.get_current_user(token)
    with session_scope() as session:
        perms = (
            session.query(models.RolePermission)
            .filter(
                models.RolePermission.role_id == user.role_id,
                models.RolePermission.is_deleted == False,
            )
            .all()
        )
        permission_codes = [p.permission_code for p in perms]
    return ok({
        "id": user.id,
        "emp_no": user.emp_no,
        "name": user.name,
        "email": user.email,
        "dept_id": user.dept_id,
        "role_id": user.role_id,
        "permissions": permission_codes,
    })


# ── 使用者管理 ─────────────────────────────────────────────────────────

@router.get("/auth/users")
def list_users(request: Request, q: str = Query(default=""), limit: int = Query(default=200, ge=1, le=500)):
    """列出所有使用者（需要 auth.user.read 權限）。"""
    auth.require_permission(auth.extract_bearer(request.headers.get("Authorization")), "auth.user.read")
    with session_scope() as session:
        query = session.query(models.User).filter(models.User.is_deleted == False)
        if q:
            query = query.filter(
                models.User.emp_no.contains(q) | models.User.name.contains(q)
            )
        users = query.order_by(models.User.emp_no).limit(limit).all()
        roles = {r.id: r.role_name for r in session.query(models.Role).filter_by(is_deleted=False).all()}
        items = [
            {
                "id": u.id, "emp_no": u.emp_no, "name": u.name,
                "email": u.email or "", "role_id": u.role_id or "",
                "role_name": roles.get(u.role_id, "") if u.role_id else "",
                "dept_id": u.dept_id or "", "is_active": u.is_active,
            }
            for u in users
        ]
    return ok({"items": items, "total": len(items)})


@router.post("/auth/users")
def create_user(request: Request, payload: schemas.UserCreate):
    """新增使用者帳號（需要 auth.user.write 權限）。"""
    auth.require_permission(auth.extract_bearer(request.headers.get("Authorization")), "auth.user.write")
    with session_scope() as session:
        if session.query(models.User).filter_by(emp_no=payload.emp_no, is_deleted=False).first():
            raise HTTPException(status_code=409, detail=f"員工編號 {payload.emp_no} 已存在")
        user = models.User(
            emp_no=payload.emp_no,
            name=payload.name,
            email=payload.email or "",
            password_hash=auth.hash_password(payload.password),
            role_id=payload.role_id,
            dept_id=payload.dept_id,
            is_active=True,
        )
        session.add(user)
        session.flush()
        new_id = user.id
    return ok({"id": new_id, "message": f"已新增使用者 {payload.emp_no}"})


@router.patch("/auth/users/{user_id}")
def update_user(request: Request, user_id: str, payload: schemas.UserUpdate):
    """修改使用者資料（名稱、角色、停用等）。"""
    auth.require_permission(auth.extract_bearer(request.headers.get("Authorization")), "auth.user.write")
    with session_scope() as session:
        user = session.query(models.User).filter_by(id=user_id, is_deleted=False).first()
        if not user:
            raise HTTPException(status_code=404, detail="使用者不存在")
        for field, value in payload.model_dump(exclude_none=True).items():
            setattr(user, field, value)
    return ok({"message": "已更新使用者資料"})


@router.post("/auth/users/{user_id}/reset-password")
def reset_user_password(request: Request, user_id: str, payload: schemas.UserPasswordReset):
    """重設指定使用者的密碼（需要 auth.user.write 權限）。"""
    auth.require_permission(auth.extract_bearer(request.headers.get("Authorization")), "auth.user.write")
    with session_scope() as session:
        user = session.query(models.User).filter_by(id=user_id, is_deleted=False).first()
        if not user:
            raise HTTPException(status_code=404, detail="使用者不存在")
        user.password_hash = auth.hash_password(payload.new_password)
    return ok({"message": "密碼已重設"})


@router.delete("/auth/users/{user_id}")
def delete_user(request: Request, user_id: str):
    """停用並刪除使用者帳號（軟刪除）。"""
    auth.require_permission(auth.extract_bearer(request.headers.get("Authorization")), "auth.user.write")
    with session_scope() as session:
        user = session.query(models.User).filter_by(id=user_id, is_deleted=False).first()
        if not user:
            raise HTTPException(status_code=404, detail="使用者不存在")
        user.is_active = False
        user.is_deleted = True
    return ok({"message": "已停用使用者"})


# ── 內部服務端點（供 v2_backend 呼叫，需帶 X-Service-Key Header）────────

@router.get("/internal/products")
def internal_list_products(request: Request, q: str = Query(default="", description="關鍵字搜尋"), limit: int = Query(default=200, ge=1, le=500)):
    """供 QMS 稽核系統讀取產品清單（不需要使用者登入，但需要服務金鑰）。"""
    auth.require_service_key(request.headers.get("X-Service-Key"))
    with session_scope() as session:
        query = session.query(models.Product).filter(models.Product.is_deleted == False)
        if q:
            query = query.filter(models.Product.product_name.contains(q) | models.Product.product_code.contains(q))
        rows = query.order_by(models.Product.product_code.asc()).limit(limit).all()
        return ok({"items": [{"id": r.id, "product_code": r.product_code, "product_name": r.product_name, "customer_part_no": r.customer_part_no, "internal_part_no": r.internal_part_no, "status": r.status} for r in rows]})


@router.get("/internal/customers")
def internal_list_customers(request: Request, q: str = Query(default="", description="關鍵字搜尋"), limit: int = Query(default=200, ge=1, le=500)):
    """供 QMS 稽核系統讀取客戶清單。"""
    auth.require_service_key(request.headers.get("X-Service-Key"))
    with session_scope() as session:
        query = session.query(models.Customer).filter(models.Customer.is_deleted == False)
        if q:
            query = query.filter(models.Customer.customer_name.contains(q) | models.Customer.customer_code.contains(q))
        rows = query.order_by(models.Customer.customer_code.asc()).limit(limit).all()
        return ok({"items": [{"id": r.id, "customer_code": r.customer_code, "customer_name": r.customer_name, "short_name": r.short_name, "status": r.status} for r in rows]})


@router.get("/internal/work-orders")
def internal_list_work_orders(request: Request, q: str = Query(default="", description="關鍵字搜尋"), limit: int = Query(default=200, ge=1, le=500)):
    """供 QMS 稽核系統讀取工單清單。"""
    auth.require_service_key(request.headers.get("X-Service-Key"))
    with session_scope() as session:
        query = session.query(models.WorkOrder).filter(models.WorkOrder.is_deleted == False)
        if q:
            query = query.filter(models.WorkOrder.wo_no.contains(q))
        rows = query.order_by(models.WorkOrder.wo_no.desc()).limit(limit).all()
        return ok({"items": [
            {
                "id": r.id,
                "wo_no": r.wo_no,
                "product_id": r.product_id,
                "so_id": r.so_id,
                "wo_status": r.wo_status,
                "planned_qty": float(r.planned_qty),
                "released_qty": float(r.released_qty),
                "good_qty": float(r.good_qty),
                "ng_qty": float(r.ng_qty),
                "start_date": str(r.start_date) if r.start_date else None,
                "finish_date": str(r.finish_date) if r.finish_date else None,
            }
            for r in rows
        ]})


@router.get("/internal/suppliers")
def internal_list_suppliers(request: Request, q: str = Query(default="", description="關鍵字搜尋"), limit: int = Query(default=200, ge=1, le=500)):
    """供 QMS 稽核系統讀取供應商清單。"""
    auth.require_service_key(request.headers.get("X-Service-Key"))
    with session_scope() as session:
        query = session.query(models.Supplier).filter(models.Supplier.is_deleted == False)
        if q:
            query = query.filter(models.Supplier.supplier_name.contains(q) | models.Supplier.supplier_code.contains(q))
        rows = query.order_by(models.Supplier.supplier_code.asc()).limit(limit).all()
        return ok({"items": [{"id": r.id, "supplier_code": r.supplier_code, "supplier_name": r.supplier_name, "category": r.category, "status": r.status} for r in rows]})
