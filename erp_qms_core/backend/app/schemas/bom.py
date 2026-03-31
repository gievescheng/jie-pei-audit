from __future__ import annotations

from pydantic import BaseModel


class BomItemCreate(BaseModel):
    material_id: str
    qty_per: float = 1.0
    loss_rate: float = 0.0
