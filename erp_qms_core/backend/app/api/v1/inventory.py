from __future__ import annotations

from fastapi import APIRouter, Depends

from ...core.security import require_roles
from ...schemas.inventory import InventoryLocationCreate, InventoryTransactionCreate
from ...services import inventory as svc

router = APIRouter()


@router.get("/inventory/locations", dependencies=[Depends(require_roles())])
def list_locations():
    return svc.list_locations()


@router.post("/inventory/locations", status_code=201, dependencies=[Depends(require_roles("admin", "qm"))])
def create_location(payload: InventoryLocationCreate):
    return svc.create_location(payload)


@router.get("/inventory/transactions", dependencies=[Depends(require_roles())])
def list_transactions():
    return svc.list_transactions()


@router.post("/inventory/transactions", status_code=201, dependencies=[Depends(require_roles("admin", "qm"))])
def create_transaction(payload: InventoryTransactionCreate):
    return svc.create_transaction(payload)
