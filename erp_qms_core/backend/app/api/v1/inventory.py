from __future__ import annotations

from fastapi import APIRouter

from ...schemas.inventory import InventoryLocationCreate, InventoryTransactionCreate
from ...services import inventory as svc

router = APIRouter()


@router.get("/inventory/locations")
def list_locations():
    return svc.list_locations()


@router.post("/inventory/locations", status_code=201)
def create_location(payload: InventoryLocationCreate):
    return svc.create_location(payload)


@router.get("/inventory/transactions")
def list_transactions():
    return svc.list_transactions()


@router.post("/inventory/transactions", status_code=201)
def create_transaction(payload: InventoryTransactionCreate):
    return svc.create_transaction(payload)
