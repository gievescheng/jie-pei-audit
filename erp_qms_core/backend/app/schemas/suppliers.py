from __future__ import annotations

from pydantic import BaseModel


class SupplierCreate(BaseModel):
    supplier_code: str
    supplier_name: str
    category: str = ""


class SupplierUpdate(BaseModel):
    supplier_name: str | None = None
    category: str | None = None
    status: str | None = None
