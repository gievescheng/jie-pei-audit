from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from ...core.security import require_roles
from ...schemas.equipment import (
    EquipmentCreate, EquipmentUpdate,
    MaintenanceRecordCreate, MaintenanceRecordUpdate,
)
from ...services import equipment as svc

router = APIRouter()


@router.get("/equipment", dependencies=[Depends(require_roles())])
def list_equipment():
    return svc.list_equipment()


@router.post("/equipment", status_code=201, dependencies=[Depends(require_roles("admin", "qm"))])
def create_equipment(payload: EquipmentCreate):
    return svc.create_equipment(payload)


@router.post("/equipment/bulk-seed", status_code=201, dependencies=[Depends(require_roles("admin", "qm"))])
def bulk_seed(items: List[EquipmentCreate]):
    return svc.bulk_seed([i.model_dump() for i in items])


@router.get("/equipment/{equipment_id}", dependencies=[Depends(require_roles())])
def get_equipment(equipment_id: str):
    return svc.get_equipment(equipment_id)


@router.put("/equipment/{equipment_id}", dependencies=[Depends(require_roles("admin", "qm"))])
def update_equipment(equipment_id: str, payload: EquipmentUpdate):
    return svc.update_equipment(equipment_id, payload)


@router.delete("/equipment/{equipment_id}", dependencies=[Depends(require_roles("admin", "qm"))])
def delete_equipment(equipment_id: str):
    return svc.delete_equipment(equipment_id)


@router.get("/equipment-records", dependencies=[Depends(require_roles())])
def list_records(equipment_id: Optional[str] = Query(default=None)):
    return svc.list_records(equipment_id=equipment_id)


@router.post("/equipment-records", status_code=201, dependencies=[Depends(require_roles("admin", "qm"))])
def create_record(payload: MaintenanceRecordCreate):
    return svc.create_record(payload)


@router.put("/equipment-records/{record_id}", dependencies=[Depends(require_roles("admin", "qm"))])
def update_record(record_id: str, payload: MaintenanceRecordUpdate):
    return svc.update_record(record_id, payload)


@router.delete("/equipment-records/{record_id}", dependencies=[Depends(require_roles("admin", "qm"))])
def delete_record(record_id: str):
    return svc.delete_record(record_id)
