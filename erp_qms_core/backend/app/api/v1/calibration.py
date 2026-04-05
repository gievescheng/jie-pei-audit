from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from ...core.security import require_roles
from ...schemas.calibration import (
    CalibrationInstrumentCreate,
    CalibrationInstrumentUpdate,
    CalibrationRecordCreate,
    CalibrationRecordUpdate,
)
from ...services import calibration as svc

router = APIRouter()


# ── Instruments ───────────────────────────────────────────────────────────────

@router.get("/calibration/instruments", dependencies=[Depends(require_roles())])
def list_instruments():
    return svc.list_instruments()


@router.post("/calibration/instruments", status_code=201, dependencies=[Depends(require_roles("admin", "qm"))])
def create_instrument(payload: CalibrationInstrumentCreate):
    return svc.create_instrument(payload)


@router.get("/calibration/instruments/{instrument_id}", dependencies=[Depends(require_roles())])
def get_instrument(instrument_id: str):
    return svc.get_instrument(instrument_id)


@router.put("/calibration/instruments/{instrument_id}", dependencies=[Depends(require_roles("admin", "qm"))])
def update_instrument(instrument_id: str, payload: CalibrationInstrumentUpdate):
    return svc.update_instrument(instrument_id, payload)


@router.delete("/calibration/instruments/{instrument_id}", dependencies=[Depends(require_roles("admin", "qm"))])
def delete_instrument(instrument_id: str):
    return svc.delete_instrument(instrument_id)


# ── Records ───────────────────────────────────────────────────────────────────

@router.get("/calibration/records", dependencies=[Depends(require_roles())])
def list_records(instrument_id: Optional[str] = Query(default=None)):
    return svc.list_records(instrument_id=instrument_id)


@router.post("/calibration/records", status_code=201, dependencies=[Depends(require_roles("admin", "qm"))])
def create_record(payload: CalibrationRecordCreate):
    return svc.create_record(payload)


@router.put("/calibration/records/{record_id}", dependencies=[Depends(require_roles("admin", "qm"))])
def update_record(record_id: str, payload: CalibrationRecordUpdate):
    return svc.update_record(record_id, payload)


@router.delete("/calibration/records/{record_id}", dependencies=[Depends(require_roles("admin", "qm"))])
def delete_record(record_id: str):
    return svc.delete_record(record_id)
