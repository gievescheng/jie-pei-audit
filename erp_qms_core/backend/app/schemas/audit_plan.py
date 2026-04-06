from __future__ import annotations

from typing import List

from pydantic import BaseModel


class AuditPlanCreate(BaseModel):
    plan_no: str
    year: int = 0
    period: str = ""
    scheduled_date: str = ""
    dept: str = ""
    scope: str = ""
    auditor: str = ""
    auditee: str = ""
    status: str = "\u8a08\u756b\u4e2d"
    actual_date: str = ""
    findings: int = 0
    nc_count: int = 0


class AuditPlanUpdate(BaseModel):
    year: int | None = None
    period: str | None = None
    scheduled_date: str | None = None
    dept: str | None = None
    scope: str | None = None
    auditor: str | None = None
    auditee: str | None = None
    status: str | None = None
    actual_date: str | None = None
    findings: int | None = None
    nc_count: int | None = None


class AuditPlanBulkSeed(BaseModel):
    records: List[AuditPlanCreate]
