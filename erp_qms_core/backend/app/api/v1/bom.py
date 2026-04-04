from __future__ import annotations

from fastapi import APIRouter, Depends

from ...core.security import require_roles
from ...schemas.bom import BomItemCreate
from ...services import bom as svc

router = APIRouter()


@router.get("/master/products/{product_id}/bom", dependencies=[Depends(require_roles())])
def list_bom(product_id: str):
    return svc.list_bom(product_id)


@router.post("/master/products/{product_id}/bom", status_code=201, dependencies=[Depends(require_roles("admin", "qm"))])
def add_bom_item(product_id: str, payload: BomItemCreate):
    return svc.add_bom_item(product_id, payload)


@router.delete("/master/products/{product_id}/bom/{bom_id}", dependencies=[Depends(require_roles("admin", "qm"))])
def delete_bom_item(product_id: str, bom_id: str):
    return svc.delete_bom_item(product_id, bom_id)
