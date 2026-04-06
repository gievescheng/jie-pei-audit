from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from ...core.security import require_roles
from ...schemas.supplier_eval import SupplierEvaluationCreate, SupplierEvaluationUpdate
from ...services import supplier_eval as svc

router = APIRouter()


@router.get("/supplier-evaluations", dependencies=[Depends(require_roles())])
def list_evaluations(supplier_id: Optional[str] = Query(default=None)):
    return svc.list_evaluations(supplier_id=supplier_id)


@router.post("/supplier-evaluations", status_code=201, dependencies=[Depends(require_roles("admin", "qm"))])
def create_evaluation(payload: SupplierEvaluationCreate):
    return svc.create_evaluation(payload)


@router.get("/supplier-evaluations/{eval_id}", dependencies=[Depends(require_roles())])
def get_evaluation(eval_id: str):
    return svc.get_evaluation(eval_id)


@router.put("/supplier-evaluations/{eval_id}", dependencies=[Depends(require_roles("admin", "qm"))])
def update_evaluation(eval_id: str, payload: SupplierEvaluationUpdate):
    return svc.update_evaluation(eval_id, payload)


@router.delete("/supplier-evaluations/{eval_id}", dependencies=[Depends(require_roles("admin", "qm"))])
def delete_evaluation(eval_id: str):
    return svc.delete_evaluation(eval_id)
