from __future__ import annotations

from typing import List

from pydantic import BaseModel


class NcCreate(BaseModel):
    nc_no: str
    nc_date: str = ""
    dept: str = ""
    nc_type: str = "\u88fd\u7a0b\u7570\u5e38"
    description: str = ""
    severity: str = "\u8f15\u5fae"
    root_cause: str = ""
    corrective_action: str = ""
    responsible: str = ""
    due_date: str = ""
    status: str = "\u5f85\u8655\u7406"
    close_date: str = ""
    effectiveness: str = ""


class NcUpdate(BaseModel):
    nc_date: str | None = None
    dept: str | None = None
    nc_type: str | None = None
    description: str | None = None
    severity: str | None = None
    root_cause: str | None = None
    corrective_action: str | None = None
    responsible: str | None = None
    due_date: str | None = None
    status: str | None = None
    close_date: str | None = None
    effectiveness: str | None = None


class NcBulkSeed(BaseModel):
    records: List[NcCreate]
