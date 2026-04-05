from __future__ import annotations

from pydantic import BaseModel


class TrainingEmployeeCreate(BaseModel):
    emp_no: str
    emp_name: str
    department: str = ""
    role: str = ""
    hire_date: str = ""
    status: str = "active"


class TrainingEmployeeUpdate(BaseModel):
    emp_name: str | None = None
    department: str | None = None
    role: str | None = None
    hire_date: str | None = None
    status: str | None = None


class TrainingRecordCreate(BaseModel):
    employee_id: str
    course_name: str
    training_date: str = ""
    training_type: str = "內訓"
    result: str = "合格"
    certificate_no: str = "無"
    validity_months: int = 0
    remarks: str = ""


class TrainingRecordUpdate(BaseModel):
    course_name: str | None = None
    training_date: str | None = None
    training_type: str | None = None
    result: str | None = None
    certificate_no: str | None = None
    validity_months: int | None = None
    remarks: str | None = None
