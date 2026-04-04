from __future__ import annotations

from fastapi import APIRouter, Depends

from ...core.security import require_roles
from ...schemas.common import StatusUpdate
from ...schemas.shipments import ShipmentCreate
from ...services import shipments as svc

router = APIRouter()


@router.get("/inventory/shipments", dependencies=[Depends(require_roles())])
def list_shipments():
    return svc.list_shipments()


@router.post("/inventory/shipments", status_code=201, dependencies=[Depends(require_roles("admin", "qm"))])
def create_shipment(payload: ShipmentCreate):
    return svc.create_shipment(payload)


@router.get("/inventory/shipments/{shipment_id}", dependencies=[Depends(require_roles())])
def get_shipment(shipment_id: str):
    return svc.get_shipment(shipment_id)


@router.put("/inventory/shipments/{shipment_id}/status", dependencies=[Depends(require_roles("admin", "qm"))])
def update_shipment_status(shipment_id: str, payload: StatusUpdate):
    return svc.update_shipment_status(shipment_id, payload)
