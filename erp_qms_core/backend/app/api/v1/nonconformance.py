from __future__ import annotations

from fastapi import APIRouter, Depends

from ...core.security import require_roles
from ...schemas.nonconformance import NcCreate, NcUpdate, NcBulkSeed
from ...services import nonconformance as svc

router = APIRouter()


@router.get("/nc/count", dependencies=[Depends(require_roles())])
def count():
    return svc.count()


@router.get("/nc", dependencies=[Depends(require_roles())])
def list_all():
    return svc.list_all()


@router.post("/nc", status_code=201, dependencies=[Depends(require_roles("admin", "qm"))])
def create(payload: NcCreate):
    return svc.create(payload)


@router.patch("/nc/{nc_no}", dependencies=[Depends(require_roles("admin", "qm"))])
def update(nc_no: str, payload: NcUpdate):
    return svc.update(nc_no, payload)


@router.delete("/nc/{nc_no}", dependencies=[Depends(require_roles("admin", "qm"))])
def delete(nc_no: str):
    return svc.delete(nc_no)


@router.post("/nc/bulk-seed", status_code=201, dependencies=[Depends(require_roles("admin", "qm"))])
def bulk_seed(payload: NcBulkSeed):
    return svc.bulk_seed(payload)
