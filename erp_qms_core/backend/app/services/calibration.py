from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.exc import IntegrityError

from ..core.db import session_scope
from ..core.errors import integrity_http_error, not_found_error
from ..core.responses import ok
from ..repositories import calibration as repo
from ..schemas.calibration import (
    CalibrationInstrumentCreate,
    CalibrationInstrumentUpdate,
    CalibrationRecordCreate,
    CalibrationRecordUpdate,
)


def _instrument_dict(row) -> dict:
    # 計算下次校正日（若沒有紀錄則由最新紀錄 next_due_date 決定）
    latest_record = row.records[0] if row.records else None
    next_due = latest_record.next_due_date if latest_record else None
    last_cal = latest_record.calibration_date if latest_record else None
    return {
        "id": row.id,
        "instrument_code": row.instrument_code,
        "instrument_name": row.instrument_name,
        "instrument_type": row.instrument_type,
        "model_no": row.model_no,
        "serial_no": row.serial_no,
        "location": row.location,
        "keeper": row.keeper,
        "brand": row.brand,
        "calib_method": row.calib_method,
        "interval_days": row.interval_days,
        "needs_msa": row.needs_msa,
        "status": row.status,
        "last_calibration_date": last_cal,
        "next_due_date": next_due,
    }


def _record_dict(row) -> dict:
    return {
        "id": row.id,
        "instrument_id": row.instrument_id,
        "calibration_date": row.calibration_date,
        "next_due_date": row.next_due_date,
        "result": row.result,
        "calibrated_by": row.calibrated_by,
        "certificate_no": row.certificate_no,
        "remarks": row.remarks,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


# ── Instruments ───────────────────────────────────────────────────────────────

def list_instruments() -> dict:
    with session_scope() as session:
        rows = repo.list_instruments(session)
        return ok([_instrument_dict(r) for r in rows])


def get_instrument(instrument_id: str) -> dict:
    with session_scope() as session:
        row = repo.get_instrument(session, instrument_id)
        if not row:
            raise not_found_error("calibration_instrument")
        return ok(_instrument_dict(row))


def create_instrument(payload: CalibrationInstrumentCreate) -> dict:
    try:
        with session_scope() as session:
            row = repo.create_instrument(session, **payload.model_dump())
            return ok({"id": row.id, "instrument_code": row.instrument_code}, message="created")
    except IntegrityError as exc:
        raise integrity_http_error(exc) from exc


def update_instrument(instrument_id: str, payload: CalibrationInstrumentUpdate) -> dict:
    with session_scope() as session:
        data = {k: v for k, v in payload.model_dump().items() if v is not None}
        row = repo.update_instrument(session, instrument_id, **data)
        if not row:
            raise not_found_error("calibration_instrument")
        return ok(_instrument_dict(row), message="updated")


def delete_instrument(instrument_id: str) -> dict:
    with session_scope() as session:
        row = repo.get_instrument(session, instrument_id)
        if not row:
            raise not_found_error("calibration_instrument")
        row.is_deleted = True
        return ok({"id": row.id}, message="deleted")


# ── Records ───────────────────────────────────────────────────────────────────

def list_records(instrument_id: str | None = None) -> dict:
    with session_scope() as session:
        rows = repo.list_records(session, instrument_id=instrument_id)
        return ok([_record_dict(r) for r in rows])


def create_record(payload: CalibrationRecordCreate) -> dict:
    try:
        with session_scope() as session:
            # 若未提供下次到期日，自動由校正日 + 儀器週期計算
            next_due = payload.next_due_date
            if not next_due:
                inst = repo.get_instrument(session, payload.instrument_id)
                if inst and payload.calibration_date:
                    cal_date = date.fromisoformat(payload.calibration_date)
                    next_due = (cal_date + timedelta(days=inst.interval_days)).isoformat()

            row = repo.create_record(
                session,
                instrument_id=payload.instrument_id,
                calibration_date=payload.calibration_date,
                next_due_date=next_due,
                result=payload.result,
                calibrated_by=payload.calibrated_by,
                certificate_no=payload.certificate_no,
                remarks=payload.remarks,
            )
            return ok(_record_dict(row), message="created")
    except IntegrityError as exc:
        raise integrity_http_error(exc) from exc


def update_record(record_id: str, payload: CalibrationRecordUpdate) -> dict:
    with session_scope() as session:
        data = {k: v for k, v in payload.model_dump().items() if v is not None}
        row = repo.update_record(session, record_id, **data)
        if not row:
            raise not_found_error("calibration_record")
        return ok(_record_dict(row), message="updated")


def delete_record(record_id: str) -> dict:
    with session_scope() as session:
        row = repo.get_record(session, record_id)
        if not row:
            raise not_found_error("calibration_record")
        row.is_deleted = True
        return ok({"id": row.id}, message="deleted")
