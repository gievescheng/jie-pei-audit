from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from ...core.security import require_roles
from ...schemas.training import (
    TrainingEmployeeCreate,
    TrainingEmployeeUpdate,
    TrainingRecordCreate,
    TrainingRecordUpdate,
)
from ...services import training as svc

router = APIRouter()


# ── Employees ─────────────────────────────────────────────────────────────────

@router.get("/training/employees", dependencies=[Depends(require_roles())])
def list_employees():
    return svc.list_employees()


@router.post("/training/employees", status_code=201, dependencies=[Depends(require_roles("admin", "qm"))])
def create_employee(payload: TrainingEmployeeCreate):
    return svc.create_employee(payload)


@router.post("/training/employees/bulk-seed", status_code=201, dependencies=[Depends(require_roles("admin", "qm"))])
def bulk_seed_employees(items: List[TrainingEmployeeCreate]):
    return svc.bulk_seed_employees([i.model_dump() for i in items])


@router.get("/training/employees/{employee_id}", dependencies=[Depends(require_roles())])
def get_employee(employee_id: str):
    return svc.get_employee(employee_id)


@router.put("/training/employees/{employee_id}", dependencies=[Depends(require_roles("admin", "qm"))])
def update_employee(employee_id: str, payload: TrainingEmployeeUpdate):
    return svc.update_employee(employee_id, payload)


@router.delete("/training/employees/{employee_id}", dependencies=[Depends(require_roles("admin", "qm"))])
def delete_employee(employee_id: str):
    return svc.delete_employee(employee_id)


# ── Records ───────────────────────────────────────────────────────────────────

@router.get("/training/records", dependencies=[Depends(require_roles())])
def list_records(employee_id: Optional[str] = Query(default=None)):
    return svc.list_records(employee_id=employee_id)


@router.post("/training/records", status_code=201, dependencies=[Depends(require_roles("admin", "qm"))])
def create_record(payload: TrainingRecordCreate):
    return svc.create_record(payload)


@router.put("/training/records/{record_id}", dependencies=[Depends(require_roles("admin", "qm"))])
def update_record(record_id: str, payload: TrainingRecordUpdate):
    return svc.update_record(record_id, payload)


@router.delete("/training/records/{record_id}", dependencies=[Depends(require_roles("admin", "qm"))])
def delete_record(record_id: str):
    return svc.delete_record(record_id)
