from __future__ import annotations

from pydantic import BaseModel


class CalibrationInstrumentCreate(BaseModel):
    instrument_code: str
    instrument_name: str
    instrument_type: str = ""
    model_no: str = ""
    serial_no: str = ""
    location: str = ""
    keeper: str = ""
    brand: str = ""
    calib_method: str = ""
    interval_days: int = 365
    needs_msa: bool = False
    status: str = "active"


class CalibrationInstrumentUpdate(BaseModel):
    instrument_name: str | None = None
    instrument_type: str | None = None
    model_no: str | None = None
    serial_no: str | None = None
    location: str | None = None
    keeper: str | None = None
    brand: str | None = None
    calib_method: str | None = None
    interval_days: int | None = None
    needs_msa: bool | None = None
    status: str | None = None


class CalibrationRecordCreate(BaseModel):
    instrument_id: str
    calibration_date: str           # "YYYY-MM-DD"
    next_due_date: str | None = None
    result: str = "合格"             # 合格 | 不合格 | 條件合格
    calibrated_by: str = ""
    certificate_no: str = ""
    remarks: str = ""


class CalibrationRecordUpdate(BaseModel):
    calibration_date: str | None = None
    next_due_date: str | None = None
    result: str | None = None
    calibrated_by: str | None = None
    certificate_no: str | None = None
    remarks: str | None = None
