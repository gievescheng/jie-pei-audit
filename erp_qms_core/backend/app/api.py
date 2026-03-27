from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import IntegrityError

from . import models, schemas
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
def list_departments():
    with session_scope() as session:
        rows = session.query(models.Department).order_by(models.Department.dept_code.asc()).all()
        return ok([{"id": row.id, "dept_code": row.dept_code, "dept_name": row.dept_name} for row in rows])


@router.post("/master/departments")
def create_department(payload: schemas.DepartmentCreate):
    try:
        with session_scope() as session:
            row = models.Department(dept_code=payload.dept_code, dept_name=payload.dept_name)
            session.add(row)
            session.flush()
            return ok({"id": row.id, "dept_code": row.dept_code, "dept_name": row.dept_name}, message="created")
    except IntegrityError as exc:
        raise _integrity_http_error(exc) from exc


@router.get("/master/roles")
def list_roles():
    with session_scope() as session:
        rows = session.query(models.Role).order_by(models.Role.role_code.asc()).all()
        return ok([{"id": row.id, "role_code": row.role_code, "role_name": row.role_name} for row in rows])


@router.post("/master/roles")
def create_role(payload: schemas.RoleCreate):
    try:
        with session_scope() as session:
            row = models.Role(role_code=payload.role_code, role_name=payload.role_name, description=payload.description)
            session.add(row)
            session.flush()
            return ok({"id": row.id, "role_code": row.role_code, "role_name": row.role_name}, message="created")
    except IntegrityError as exc:
        raise _integrity_http_error(exc) from exc


@router.get("/master/customers")
def list_customers():
    with session_scope() as session:
        rows = session.query(models.Customer).order_by(models.Customer.customer_code.asc()).all()
        return ok([{"id": row.id, "customer_code": row.customer_code, "customer_name": row.customer_name} for row in rows])


@router.post("/master/customers")
def create_customer(payload: schemas.CustomerCreate):
    try:
        with session_scope() as session:
            row = models.Customer(customer_code=payload.customer_code, customer_name=payload.customer_name, short_name=payload.short_name)
            session.add(row)
            session.flush()
            return ok({"id": row.id, "customer_code": row.customer_code, "customer_name": row.customer_name}, message="created")
    except IntegrityError as exc:
        raise _integrity_http_error(exc) from exc


@router.get("/master/suppliers")
def list_suppliers():
    with session_scope() as session:
        rows = session.query(models.Supplier).order_by(models.Supplier.supplier_code.asc()).all()
        return ok([{"id": row.id, "supplier_code": row.supplier_code, "supplier_name": row.supplier_name} for row in rows])


@router.post("/master/suppliers")
def create_supplier(payload: schemas.SupplierCreate):
    try:
        with session_scope() as session:
            row = models.Supplier(supplier_code=payload.supplier_code, supplier_name=payload.supplier_name, category=payload.category)
            session.add(row)
            session.flush()
            return ok({"id": row.id, "supplier_code": row.supplier_code, "supplier_name": row.supplier_name}, message="created")
    except IntegrityError as exc:
        raise _integrity_http_error(exc) from exc


@router.get("/master/products")
def list_products():
    with session_scope() as session:
        rows = session.query(models.Product).order_by(models.Product.product_code.asc()).all()
        return ok([{"id": row.id, "product_code": row.product_code, "product_name": row.product_name} for row in rows])


@router.post("/master/products")
def create_product(payload: schemas.ProductCreate):
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


@router.get("/inventory/locations")
def list_locations():
    with session_scope() as session:
        rows = session.query(models.InventoryLocation).order_by(models.InventoryLocation.location_code.asc()).all()
        return ok([{"id": row.id, "location_code": row.location_code, "location_name": row.location_name} for row in rows])


@router.post("/inventory/locations")
def create_location(payload: schemas.InventoryLocationCreate):
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


@router.get("/orders/sales-orders")
def list_sales_orders():
    with session_scope() as session:
        rows = session.query(models.SalesOrder).order_by(models.SalesOrder.so_no.asc()).all()
        return ok([{"id": row.id, "so_no": row.so_no, "order_status": row.order_status} for row in rows])


@router.post("/orders/sales-orders")
def create_sales_order(payload: schemas.SalesOrderCreate):
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


@router.get("/orders/work-orders")
def list_work_orders():
    with session_scope() as session:
        rows = session.query(models.WorkOrder).order_by(models.WorkOrder.wo_no.asc()).all()
        return ok([{"id": row.id, "wo_no": row.wo_no, "wo_status": row.wo_status} for row in rows])


@router.post("/orders/work-orders")
def create_work_order(payload: schemas.WorkOrderCreate):
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
