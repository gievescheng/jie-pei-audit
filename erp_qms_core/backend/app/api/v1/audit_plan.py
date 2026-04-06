from __future__ import annotations

from fastapi import APIRouter, Depends

from ...core.security import require_roles
from ...schemas.audit_plan import AuditPlanCreate, AuditPlanUpdate, AuditPlanBulkSeed
from ...services import audit_plan as svc

router = APIRouter()


@router.get("/audit-plans/count", dependencies=[Depends(require_roles())])
def count():
    return svc.count()


@router.get("/audit-plans", dependencies=[Depends(require_roles())])
def list_all():
    return svc.list_all()


@router.post("/audit-plans", status_code=201, dependencies=[Depends(require_roles("admin", "qm"))])
def create(payload: AuditPlanCreate):
    return svc.create(payload)


@router.patch("/audit-plans/{plan_no}", dependencies=[Depends(require_roles("admin", "qm"))])
def update(plan_no: str, payload: AuditPlanUpdate):
    return svc.update(plan_no, payload)


@router.delete("/audit-plans/{plan_no}", dependencies=[Depends(require_roles("admin", "qm"))])
def delete(plan_no: str):
    return svc.delete(plan_no)


@router.post("/audit-plans/bulk-seed", status_code=201, dependencies=[Depends(require_roles("admin", "qm"))])
def bulk_seed(payload: AuditPlanBulkSeed):
    return svc.bulk_seed(payload)
