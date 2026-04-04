from __future__ import annotations

from fastapi import APIRouter, Depends

from ...core.security import require_roles
from ...schemas.suppliers import SupplierCreate, SupplierUpdate
from ...services import suppliers as svc

router = APIRouter()


@router.get("/master/suppliers", dependencies=[Depends(require_roles())])
def list_suppliers():
    return svc.list_suppliers()


@router.post("/master/suppliers", status_code=201, dependencies=[Depends(require_roles("admin", "qm"))])
def create_supplier(payload: SupplierCreate):
    return svc.create_supplier(payload)


@router.get("/master/suppliers/{supplier_id}", dependencies=[Depends(require_roles())])
def get_supplier(supplier_id: str):
    return svc.get_supplier(supplier_id)


@router.put("/master/suppliers/{supplier_id}", dependencies=[Depends(require_roles("admin", "qm"))])
def update_supplier(supplier_id: str, payload: SupplierUpdate):
    return svc.update_supplier(supplier_id, payload)
