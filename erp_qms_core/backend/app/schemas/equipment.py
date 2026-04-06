from __future__ import annotations
from typing import List
from pydantic import BaseModel


class EquipmentCreate(BaseModel):
    equip_no: str
    equip_name: str
    location: str = ""
    model_no: str = ""
    serial_no: str = ""
    brand: str = ""
    interval_days: int = 90
    maint_items: str = "[]"   # JSON array string
    status: str = "active"


class EquipmentUpdate(BaseModel):
    equip_name: str | None = None
    location: str | None = None
    model_no: str | None = None
    serial_no: str | None = None
    brand: str | None = None
    interval_days: int | None = None
    maint_items: str | None = None
    status: str | None = None


class MaintenanceRecordCreate(BaseModel):
    equipment_id: str
    maint_date: str              # "YYYY-MM-DD"
    performed_by: str = ""
    items_done: str = "[]"       # JSON array string
    result: str = "正常"
    remarks: str = ""


class MaintenanceRecordUpdate(BaseModel):
    maint_date: str | None = None
    performed_by: str | None = None
    items_done: str | None = None
    result: str | None = None
    remarks: str | None = None
