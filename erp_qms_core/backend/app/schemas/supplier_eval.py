from __future__ import annotations
from pydantic import BaseModel


class SupplierEvaluationCreate(BaseModel):
    supplier_id: str
    eval_date: str               # "YYYY-MM-DD"
    eval_score: int = 0
    eval_result: str = "合格"   # 優良/合格/條件合格/不合格
    eval_by: str = ""
    issues: str = "[]"           # JSON array string
    remarks: str = ""
    next_eval_date: str | None = None


class SupplierEvaluationUpdate(BaseModel):
    eval_date: str | None = None
    eval_score: int | None = None
    eval_result: str | None = None
    eval_by: str | None = None
    issues: str | None = None
    remarks: str | None = None
    next_eval_date: str | None = None
