from __future__ import annotations

from pydantic import BaseModel


class StatusUpdate(BaseModel):
    status: str


class WorkOrderQtyUpdate(BaseModel):
    good_qty: float = 0
    ng_qty: float = 0
