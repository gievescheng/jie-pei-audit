from __future__ import annotations

from pydantic import BaseModel


class DepartmentCreate(BaseModel):
    dept_code: str
    dept_name: str


class RoleCreate(BaseModel):
    role_code: str
    role_name: str
    description: str = ""


class MaterialMasterCreate(BaseModel):
    material_code: str
    material_name: str
    material_type: str = "raw"
    unit: str = "PCS"


class MaterialMasterUpdate(BaseModel):
    material_name: str | None = None
    material_type: str | None = None
    unit: str | None = None
    status: str | None = None


class ShiftMasterCreate(BaseModel):
    shift_code: str
    shift_name: str
    start_time: str = "08:00"
    end_time: str = "17:00"
