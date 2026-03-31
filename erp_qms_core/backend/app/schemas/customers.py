from __future__ import annotations

from pydantic import BaseModel


class CustomerCreate(BaseModel):
    customer_code: str
    customer_name: str
    short_name: str = ""


class CustomerUpdate(BaseModel):
    customer_name: str | None = None
    short_name: str | None = None
    status: str | None = None
