from __future__ import annotations

from sqlalchemy.orm import Session

from ..models.calibration import CalibrationInstrument, CalibrationRecord


# ── Instruments ───────────────────────────────────────────────────────────────

def list_instruments(session: Session) -> list[CalibrationInstrument]:
    return (
        session.query(CalibrationInstrument)
        .filter(CalibrationInstrument.is_deleted == False)  # noqa: E712
        .order_by(CalibrationInstrument.instrument_code.asc())
        .all()
    )


def get_instrument(session: Session, instrument_id: str) -> CalibrationInstrument | None:
    return (
        session.query(CalibrationInstrument)
        .filter(
            CalibrationInstrument.id == instrument_id,
            CalibrationInstrument.is_deleted == False,  # noqa: E712
        )
        .first()
    )


def create_instrument(session: Session, **kwargs) -> CalibrationInstrument:
    row = CalibrationInstrument(**kwargs)
    session.add(row)
    session.flush()
    return row


def update_instrument(
    session: Session, instrument_id: str, **kwargs
) -> CalibrationInstrument | None:
    row = get_instrument(session, instrument_id)
    if not row:
        return None
    for k, v in kwargs.items():
        if v is not None:
            setattr(row, k, v)
    session.flush()
    return row


# ── Records ───────────────────────────────────────────────────────────────────

def list_records(
    session: Session, instrument_id: str | None = None
) -> list[CalibrationRecord]:
    q = (
        session.query(CalibrationRecord)
        .filter(CalibrationRecord.is_deleted == False)  # noqa: E712
    )
    if instrument_id:
        q = q.filter(CalibrationRecord.instrument_id == instrument_id)
    return q.order_by(CalibrationRecord.calibration_date.desc()).all()


def get_record(session: Session, record_id: str) -> CalibrationRecord | None:
    return (
        session.query(CalibrationRecord)
        .filter(
            CalibrationRecord.id == record_id,
            CalibrationRecord.is_deleted == False,  # noqa: E712
        )
        .first()
    )


def create_record(session: Session, **kwargs) -> CalibrationRecord:
    row = CalibrationRecord(**kwargs)
    session.add(row)
    session.flush()
    return row


def update_record(
    session: Session, record_id: str, **kwargs
) -> CalibrationRecord | None:
    row = get_record(session, record_id)
    if not row:
        return None
    for k, v in kwargs.items():
        if v is not None:
            setattr(row, k, v)
    session.flush()
    return row
