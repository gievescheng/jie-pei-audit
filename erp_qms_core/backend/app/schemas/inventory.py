from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class InventoryLocationCreate(BaseModel):
    location_code: str
    location_name: str
    location_type: str = "warehouse"
    is_hold_area: bool = False


class InventoryTransactionCreate(BaseModel):
    trx_no: str
    trx_type: str
    item_type: str
    item_ref_id: str = ""
    lot_no: str = ""
    qty: float = 0
    location_code: str = ""
    inventory_status: str = "available"
    trx_date: date | None = None
