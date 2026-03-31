from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class ShipmentCreate(BaseModel):
    shipment_no: str
    so_id: str | None = None
    shipment_date: date | None = None
    ship_status: str = "draft"
    remark: str = ""
