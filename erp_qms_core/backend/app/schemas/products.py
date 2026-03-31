from __future__ import annotations

from pydantic import BaseModel


class ProductCreate(BaseModel):
    product_code: str
    product_name: str
    customer_part_no: str = ""
    internal_part_no: str = ""
    spec_summary: str = ""


class ProductUpdate(BaseModel):
    product_name: str | None = None
    customer_part_no: str | None = None
    internal_part_no: str | None = None
    spec_summary: str | None = None
    status: str | None = None
