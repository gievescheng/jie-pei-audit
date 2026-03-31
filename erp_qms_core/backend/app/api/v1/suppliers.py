from __future__ import annotations

from fastapi import APIRouter

from ...schemas.suppliers import SupplierCreate, SupplierUpdate
from ...services import suppliers as svc

router = APIRouter()


@router.get("/master/suppliers")
def list_suppliers():
    return svc.list_suppliers()


@router.post("/master/suppliers", status_code=201)
def create_supplier(payload: SupplierCreate):
    return svc.create_supplier(payload)


@router.get("/master/suppliers/{supplier_id}")
def get_supplier(supplier_id: str):
    return svc.get_supplier(supplier_id)


@router.put("/master/suppliers/{supplier_id}")
def update_supplier(supplier_id: str, payload: SupplierUpdate):
    return svc.update_supplier(supplier_id, payload)
