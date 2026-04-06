from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from ...core.security import require_roles
from ...schemas.env_particle import EnvParticleRecordCreate, EnvParticleBulkSeed
from ...services import env_particle as svc

router = APIRouter()


@router.get("/env-particle/count", dependencies=[Depends(require_roles())])
def count_records():
    return svc.count()


@router.get("/env-particle", dependencies=[Depends(require_roles())])
def list_records(
    date_from: Optional[str] = Query(default=None),
    date_to: Optional[str] = Query(default=None),
    limit: int = Query(default=500, le=1000),
    offset: int = Query(default=0),
):
    return svc.list_records(date_from=date_from, date_to=date_to, limit=limit, offset=offset)


@router.post("/env-particle", status_code=201, dependencies=[Depends(require_roles("admin", "qm"))])
def create_record(payload: EnvParticleRecordCreate):
    return svc.create_record(payload)


@router.post("/env-particle/bulk-seed", status_code=201, dependencies=[Depends(require_roles("admin", "qm"))])
def bulk_seed(payload: EnvParticleBulkSeed):
    return svc.bulk_seed(payload)
