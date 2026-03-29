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


def _not_found(resource: str) -> HTTPException:
    return HTTPException(status_code=404, detail=f"{resource} not found")


# ── 健康檢查 ─────────────────────────────────────────────────

@router.get("/health")
def health():
    return ok({"service": "jepe-erp-qms-core"}, message="healthy")


# ── 主資料：部門 ─────────────────────────────────────────────

@router.get("/master/departments")
def list_departments():
    with session_scope() as session:
        rows = session.query(models.Department).order_by(models.Department.dept_code.asc()).all()
        return ok([{"id": row.id, "dept_code": row.dept_code, "dept_name": row.dept_name} for row in rows])


@router.post("/master/departments", status_code=201)
def create_department(payload: schemas.DepartmentCreate):
    try:
        with session_scope() as session:
            row = models.Department(dept_code=payload.dept_code, dept_name=payload.dept_name)
            session.add(row)
            session.flush()
            return ok({"id": row.id, "dept_code": row.dept_code, "dept_name": row.dept_name}, message="created")
    except IntegrityError as exc:
        raise _integrity_http_error(exc) from exc


# ── 主資料：角色 ─────────────────────────────────────────────

@router.get("/master/roles")
def list_roles():
    with session_scope() as session:
        rows = session.query(models.Role).order_by(models.Role.role_code.asc()).all()
        return ok([{"id": row.id, "role_code": row.role_code, "role_name": row.role_name} for row in rows])


@router.post("/master/roles", status_code=201)
def create_role(payload: schemas.RoleCreate):
    try:
        with session_scope() as session:
            row = models.Role(role_code=payload.role_code, role_name=payload.role_name, description=payload.description)
            session.add(row)
            session.flush()
            return ok({"id": row.id, "role_code": row.role_code, "role_name": row.role_name}, message="created")
    except IntegrityError as exc:
        raise _integrity_http_error(exc) from exc


# ── 主資料：客戶 ─────────────────────────────────────────────

@router.get("/master/customers")
def list_customers():
    with session_scope() as session:
        rows = session.query(models.Customer).filter(models.Customer.is_deleted == False).order_by(models.Customer.customer_code.asc()).all()
        return ok([{"id": row.id, "customer_code": row.customer_code, "customer_name": row.customer_name, "short_name": row.short_name, "status": row.status} for row in rows])


@router.post("/master/customers", status_code=201)
def create_customer(payload: schemas.CustomerCreate):
    try:
        with session_scope() as session:
            row = models.Customer(customer_code=payload.customer_code, customer_name=payload.customer_name, short_name=payload.short_name)
            session.add(row)
            session.flush()
            return ok({"id": row.id, "customer_code": row.customer_code, "customer_name": row.customer_name}, message="created")
    except IntegrityError as exc:
        raise _integrity_http_error(exc) from exc


@router.get("/master/customers/{customer_id}")
def get_customer(customer_id: str):
    with session_scope() as session:
        row = session.query(models.Customer).filter(models.Customer.id == customer_id, models.Customer.is_deleted == False).first()
        if not row:
            raise _not_found("customer")
        return ok({"id": row.id, "customer_code": row.customer_code, "customer_name": row.customer_name, "short_name": row.short_name, "status": row.status})


@router.put("/master/customers/{customer_id}")
def update_customer(customer_id: str, payload: schemas.CustomerUpdate):
    with session_scope() as session:
        row = session.query(models.Customer).filter(models.Customer.id == customer_id, models.Customer.is_deleted == False).first()
        if not row:
            raise _not_found("customer")
        if payload.customer_name is not None:
            row.customer_name = payload.customer_name
        if payload.short_name is not None:
            row.short_name = payload.short_name
        if payload.status is not None:
            row.status = payload.status
        return ok({"id": row.id, "customer_code": row.customer_code, "customer_name": row.customer_name, "status": row.status}, message="updated")


# ── 主資料：供應商 ───────────────────────────────────────────

@router.get("/master/suppliers")
def list_suppliers():
    with session_scope() as session:
        rows = session.query(models.Supplier).filter(models.Supplier.is_deleted == False).order_by(models.Supplier.supplier_code.asc()).all()
        return ok([{"id": row.id, "supplier_code": row.supplier_code, "supplier_name": row.supplier_name, "category": row.category, "status": row.status} for row in rows])


@router.post("/master/suppliers", status_code=201)
def create_supplier(payload: schemas.SupplierCreate):
    try:
        with session_scope() as session:
            row = models.Supplier(supplier_code=payload.supplier_code, supplier_name=payload.supplier_name, category=payload.category)
            session.add(row)
            session.flush()
            return ok({"id": row.id, "supplier_code": row.supplier_code, "supplier_name": row.supplier_name}, message="created")
    except IntegrityError as exc:
        raise _integrity_http_error(exc) from exc


@router.get("/master/suppliers/{supplier_id}")
def get_supplier(supplier_id: str):
    with session_scope() as session:
        row = session.query(models.Supplier).filter(models.Supplier.id == supplier_id, models.Supplier.is_deleted == False).first()
        if not row:
            raise _not_found("supplier")
        return ok({"id": row.id, "supplier_code": row.supplier_code, "supplier_name": row.supplier_name, "category": row.category, "status": row.status})


@router.put("/master/suppliers/{supplier_id}")
def update_supplier(supplier_id: str, payload: schemas.SupplierUpdate):
    with session_scope() as session:
        row = session.query(models.Supplier).filter(models.Supplier.id == supplier_id, models.Supplier.is_deleted == False).first()
        if not row:
            raise _not_found("supplier")
        if payload.supplier_name is not None:
            row.supplier_name = payload.supplier_name
        if payload.category is not None:
            row.category = payload.category
        if payload.status is not None:
            row.status = payload.status
        return ok({"id": row.id, "supplier_code": row.supplier_code, "supplier_name": row.supplier_name, "status": row.status}, message="updated")


# ── 主資料：產品 ─────────────────────────────────────────────

@router.get("/master/products")
def list_products():
    with session_scope() as session:
        rows = session.query(models.Product).filter(models.Product.is_deleted == False).order_by(models.Product.product_code.asc()).all()
        return ok([{"id": row.id, "product_code": row.product_code, "product_name": row.product_name, "customer_part_no": row.customer_part_no, "internal_part_no": row.internal_part_no, "status": row.status} for row in rows])


@router.post("/master/products", status_code=201)
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


@router.get("/master/products/{product_id}")
def get_product(product_id: str):
    with session_scope() as session:
        row = session.query(models.Product).filter(models.Product.id == product_id, models.Product.is_deleted == False).first()
        if not row:
            raise _not_found("product")
        return ok({"id": row.id, "product_code": row.product_code, "product_name": row.product_name, "customer_part_no": row.customer_part_no, "internal_part_no": row.internal_part_no, "spec_summary": row.spec_summary, "status": row.status})


@router.put("/master/products/{product_id}")
def update_product(product_id: str, payload: schemas.ProductUpdate):
    with session_scope() as session:
        row = session.query(models.Product).filter(models.Product.id == product_id, models.Product.is_deleted == False).first()
        if not row:
            raise _not_found("product")
        if payload.product_name is not None:
            row.product_name = payload.product_name
        if payload.customer_part_no is not None:
            row.customer_part_no = payload.customer_part_no
        if payload.internal_part_no is not None:
            row.internal_part_no = payload.internal_part_no
        if payload.spec_summary is not None:
            row.spec_summary = payload.spec_summary
        if payload.status is not None:
            row.status = payload.status
        return ok({"id": row.id, "product_code": row.product_code, "product_name": row.product_name, "status": row.status}, message="updated")


# ── 主資料：BOM ──────────────────────────────────────────────

@router.get("/master/products/{product_id}/bom")
def list_bom(product_id: str):
    with session_scope() as session:
        product = session.query(models.Product).filter(models.Product.id == product_id).first()
        if not product:
            raise _not_found("product")
        rows = session.query(models.BomItem).filter(models.BomItem.product_id == product_id, models.BomItem.is_deleted == False).all()
        return ok([{"id": row.id, "material_id": row.material_id, "qty_per": float(row.qty_per), "loss_rate": float(row.loss_rate)} for row in rows])


@router.post("/master/products/{product_id}/bom", status_code=201)
def add_bom_item(product_id: str, payload: schemas.BomItemCreate):
    try:
        with session_scope() as session:
            product = session.query(models.Product).filter(models.Product.id == product_id).first()
            if not product:
                raise _not_found("product")
            row = models.BomItem(product_id=product_id, material_id=payload.material_id, qty_per=payload.qty_per, loss_rate=payload.loss_rate)
            session.add(row)
            session.flush()
            return ok({"id": row.id, "product_id": row.product_id, "material_id": row.material_id, "qty_per": float(row.qty_per)}, message="created")
    except IntegrityError as exc:
        raise _integrity_http_error(exc) from exc


@router.delete("/master/products/{product_id}/bom/{bom_id}")
def delete_bom_item(product_id: str, bom_id: str):
    with session_scope() as session:
        row = session.query(models.BomItem).filter(models.BomItem.id == bom_id, models.BomItem.product_id == product_id).first()
        if not row:
            raise _not_found("bom item")
        row.is_deleted = True
        return ok({"id": bom_id}, message="deleted")


# ── 主資料：材料主檔 ─────────────────────────────────────────

@router.get("/master/materials")
def list_materials():
    with session_scope() as session:
        rows = session.query(models.MaterialMaster).filter(models.MaterialMaster.is_deleted == False).order_by(models.MaterialMaster.material_code.asc()).all()
        return ok([{"id": row.id, "material_code": row.material_code, "material_name": row.material_name, "material_type": row.material_type, "unit": row.unit, "status": row.status} for row in rows])


@router.post("/master/materials", status_code=201)
def create_material(payload: schemas.MaterialMasterCreate):
    try:
        with session_scope() as session:
            row = models.MaterialMaster(material_code=payload.material_code, material_name=payload.material_name, material_type=payload.material_type, unit=payload.unit)
            session.add(row)
            session.flush()
            return ok({"id": row.id, "material_code": row.material_code, "material_name": row.material_name}, message="created")
    except IntegrityError as exc:
        raise _integrity_http_error(exc) from exc


@router.get("/master/materials/{material_id}")
def get_material(material_id: str):
    with session_scope() as session:
        row = session.query(models.MaterialMaster).filter(models.MaterialMaster.id == material_id, models.MaterialMaster.is_deleted == False).first()
        if not row:
            raise _not_found("material")
        return ok({"id": row.id, "material_code": row.material_code, "material_name": row.material_name, "material_type": row.material_type, "unit": row.unit, "status": row.status})


@router.put("/master/materials/{material_id}")
def update_material(material_id: str, payload: schemas.MaterialMasterUpdate):
    with session_scope() as session:
        row = session.query(models.MaterialMaster).filter(models.MaterialMaster.id == material_id, models.MaterialMaster.is_deleted == False).first()
        if not row:
            raise _not_found("material")
        if payload.material_name is not None:
            row.material_name = payload.material_name
        if payload.material_type is not None:
            row.material_type = payload.material_type
        if payload.unit is not None:
            row.unit = payload.unit
        if payload.status is not None:
            row.status = payload.status
        return ok({"id": row.id, "material_code": row.material_code, "material_name": row.material_name, "status": row.status}, message="updated")


# ── 主資料：班次 ─────────────────────────────────────────────

@router.get("/master/shifts")
def list_shifts():
    with session_scope() as session:
        rows = session.query(models.ShiftMaster).filter(models.ShiftMaster.is_deleted == False).order_by(models.ShiftMaster.shift_code.asc()).all()
        return ok([{"id": row.id, "shift_code": row.shift_code, "shift_name": row.shift_name, "start_time": row.start_time, "end_time": row.end_time} for row in rows])


@router.post("/master/shifts", status_code=201)
def create_shift(payload: schemas.ShiftMasterCreate):
    try:
        with session_scope() as session:
            row = models.ShiftMaster(shift_code=payload.shift_code, shift_name=payload.shift_name, start_time=payload.start_time, end_time=payload.end_time)
            session.add(row)
            session.flush()
            return ok({"id": row.id, "shift_code": row.shift_code, "shift_name": row.shift_name}, message="created")
    except IntegrityError as exc:
        raise _integrity_http_error(exc) from exc


# ── 庫存：儲位 ───────────────────────────────────────────────

@router.get("/inventory/locations")
def list_locations():
    with session_scope() as session:
        rows = session.query(models.InventoryLocation).filter(models.InventoryLocation.is_deleted == False).order_by(models.InventoryLocation.location_code.asc()).all()
        return ok([{"id": row.id, "location_code": row.location_code, "location_name": row.location_name, "location_type": row.location_type, "is_hold_area": row.is_hold_area} for row in rows])


@router.post("/inventory/locations", status_code=201)
def create_location(payload: schemas.InventoryLocationCreate):
    try:
        with session_scope() as session:
            row = models.InventoryLocation(location_code=payload.location_code, location_name=payload.location_name, location_type=payload.location_type, is_hold_area=payload.is_hold_area)
            session.add(row)
            session.flush()
            return ok({"id": row.id, "location_code": row.location_code, "location_name": row.location_name}, message="created")
    except IntegrityError as exc:
        raise _integrity_http_error(exc) from exc


# ── 庫存：異動 ───────────────────────────────────────────────

@router.get("/inventory/transactions")
def list_transactions():
    with session_scope() as session:
        rows = session.query(models.InventoryTransaction).order_by(models.InventoryTransaction.trx_date.desc()).limit(200).all()
        return ok([{"id": row.id, "trx_no": row.trx_no, "trx_type": row.trx_type, "lot_no": row.lot_no, "qty": float(row.qty), "location_code": row.location_code, "inventory_status": row.inventory_status, "trx_date": str(row.trx_date) if row.trx_date else None} for row in rows])


@router.post("/inventory/transactions", status_code=201)
def create_transaction(payload: schemas.InventoryTransactionCreate):
    try:
        with session_scope() as session:
            row = models.InventoryTransaction(
                trx_no=payload.trx_no,
                trx_type=payload.trx_type,
                item_type=payload.item_type,
                item_ref_id=payload.item_ref_id,
                lot_no=payload.lot_no,
                qty=payload.qty,
                location_code=payload.location_code,
                inventory_status=payload.inventory_status,
                trx_date=payload.trx_date,
            )
            session.add(row)
            session.flush()
            return ok({"id": row.id, "trx_no": row.trx_no, "trx_type": row.trx_type, "qty": float(row.qty)}, message="created")
    except IntegrityError as exc:
        raise _integrity_http_error(exc) from exc


# ── 訂單：銷售訂單 ───────────────────────────────────────────

@router.get("/orders/sales-orders")
def list_sales_orders():
    with session_scope() as session:
        rows = session.query(models.SalesOrder).filter(models.SalesOrder.is_deleted == False).order_by(models.SalesOrder.so_no.asc()).all()
        return ok([{"id": row.id, "so_no": row.so_no, "customer_id": row.customer_id, "order_date": str(row.order_date) if row.order_date else None, "due_date": str(row.due_date) if row.due_date else None, "order_status": row.order_status} for row in rows])


@router.post("/orders/sales-orders", status_code=201)
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


@router.get("/orders/sales-orders/{so_id}")
def get_sales_order(so_id: str):
    with session_scope() as session:
        row = session.query(models.SalesOrder).filter(models.SalesOrder.id == so_id, models.SalesOrder.is_deleted == False).first()
        if not row:
            raise _not_found("sales order")
        items = session.query(models.SalesOrderItem).filter(models.SalesOrderItem.so_id == so_id, models.SalesOrderItem.is_deleted == False).all()
        return ok({
            "id": row.id, "so_no": row.so_no, "customer_id": row.customer_id,
            "order_date": str(row.order_date) if row.order_date else None,
            "due_date": str(row.due_date) if row.due_date else None,
            "order_status": row.order_status, "special_requirement": row.special_requirement,
            "items": [{"id": i.id, "product_id": i.product_id, "ordered_qty": float(i.ordered_qty), "unit": i.unit, "remark": i.remark} for i in items],
        })


@router.put("/orders/sales-orders/{so_id}/status")
def update_sales_order_status(so_id: str, payload: schemas.StatusUpdate):
    with session_scope() as session:
        row = session.query(models.SalesOrder).filter(models.SalesOrder.id == so_id, models.SalesOrder.is_deleted == False).first()
        if not row:
            raise _not_found("sales order")
        row.order_status = payload.status
        return ok({"id": row.id, "so_no": row.so_no, "order_status": row.order_status}, message="updated")


@router.post("/orders/sales-orders/{so_id}/items", status_code=201)
def add_sales_order_item(so_id: str, payload: schemas.SalesOrderItemCreate):
    try:
        with session_scope() as session:
            so = session.query(models.SalesOrder).filter(models.SalesOrder.id == so_id).first()
            if not so:
                raise _not_found("sales order")
            row = models.SalesOrderItem(so_id=so_id, product_id=payload.product_id, ordered_qty=payload.ordered_qty, unit=payload.unit, remark=payload.remark)
            session.add(row)
            session.flush()
            return ok({"id": row.id, "so_id": row.so_id, "product_id": row.product_id, "ordered_qty": float(row.ordered_qty)}, message="created")
    except IntegrityError as exc:
        raise _integrity_http_error(exc) from exc


# ── 訂單：工單 ───────────────────────────────────────────────

@router.get("/orders/work-orders")
def list_work_orders():
    with session_scope() as session:
        rows = session.query(models.WorkOrder).filter(models.WorkOrder.is_deleted == False).order_by(models.WorkOrder.wo_no.asc()).all()
        return ok([{"id": row.id, "wo_no": row.wo_no, "so_id": row.so_id, "product_id": row.product_id, "planned_qty": float(row.planned_qty), "good_qty": float(row.good_qty), "ng_qty": float(row.ng_qty), "wo_status": row.wo_status} for row in rows])


@router.post("/orders/work-orders", status_code=201)
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


@router.get("/orders/work-orders/{wo_id}")
def get_work_order(wo_id: str):
    with session_scope() as session:
        row = session.query(models.WorkOrder).filter(models.WorkOrder.id == wo_id, models.WorkOrder.is_deleted == False).first()
        if not row:
            raise _not_found("work order")
        return ok({
            "id": row.id, "wo_no": row.wo_no, "so_id": row.so_id, "product_id": row.product_id,
            "planned_qty": float(row.planned_qty), "released_qty": float(row.released_qty),
            "good_qty": float(row.good_qty), "ng_qty": float(row.ng_qty),
            "wo_status": row.wo_status,
            "start_date": str(row.start_date) if row.start_date else None,
            "finish_date": str(row.finish_date) if row.finish_date else None,
        })


@router.put("/orders/work-orders/{wo_id}/status")
def update_work_order_status(wo_id: str, payload: schemas.StatusUpdate):
    with session_scope() as session:
        row = session.query(models.WorkOrder).filter(models.WorkOrder.id == wo_id, models.WorkOrder.is_deleted == False).first()
        if not row:
            raise _not_found("work order")
        row.wo_status = payload.status
        return ok({"id": row.id, "wo_no": row.wo_no, "wo_status": row.wo_status}, message="updated")


@router.put("/orders/work-orders/{wo_id}/qty")
def update_work_order_qty(wo_id: str, payload: schemas.WorkOrderQtyUpdate):
    with session_scope() as session:
        row = session.query(models.WorkOrder).filter(models.WorkOrder.id == wo_id, models.WorkOrder.is_deleted == False).first()
        if not row:
            raise _not_found("work order")
        row.good_qty = payload.good_qty
        row.ng_qty = payload.ng_qty
        return ok({"id": row.id, "wo_no": row.wo_no, "good_qty": float(row.good_qty), "ng_qty": float(row.ng_qty)}, message="updated")


# ── 出貨 ─────────────────────────────────────────────────────

@router.get("/inventory/shipments")
def list_shipments():
    with session_scope() as session:
        rows = session.query(models.Shipment).filter(models.Shipment.is_deleted == False).order_by(models.Shipment.shipment_no.asc()).all()
        return ok([{"id": row.id, "shipment_no": row.shipment_no, "so_id": row.so_id, "shipment_date": str(row.shipment_date) if row.shipment_date else None, "ship_status": row.ship_status} for row in rows])


@router.post("/inventory/shipments", status_code=201)
def create_shipment(payload: schemas.ShipmentCreate):
    try:
        with session_scope() as session:
            row = models.Shipment(
                shipment_no=payload.shipment_no,
                so_id=payload.so_id,
                shipment_date=payload.shipment_date,
                ship_status=payload.ship_status,
                remark=payload.remark,
            )
            session.add(row)
            session.flush()
            return ok({"id": row.id, "shipment_no": row.shipment_no, "ship_status": row.ship_status}, message="created")
    except IntegrityError as exc:
        raise _integrity_http_error(exc) from exc


@router.get("/inventory/shipments/{shipment_id}")
def get_shipment(shipment_id: str):
    with session_scope() as session:
        row = session.query(models.Shipment).filter(models.Shipment.id == shipment_id, models.Shipment.is_deleted == False).first()
        if not row:
            raise _not_found("shipment")
        return ok({"id": row.id, "shipment_no": row.shipment_no, "so_id": row.so_id, "shipment_date": str(row.shipment_date) if row.shipment_date else None, "ship_status": row.ship_status, "remark": row.remark})


@router.put("/inventory/shipments/{shipment_id}/status")
def update_shipment_status(shipment_id: str, payload: schemas.StatusUpdate):
    with session_scope() as session:
        row = session.query(models.Shipment).filter(models.Shipment.id == shipment_id, models.Shipment.is_deleted == False).first()
        if not row:
            raise _not_found("shipment")
        row.ship_status = payload.status
        return ok({"id": row.id, "shipment_no": row.shipment_no, "ship_status": row.ship_status}, message="updated")
