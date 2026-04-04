from __future__ import annotations

from fastapi import APIRouter, Depends

from ...core.security import require_roles
from ...schemas.customers import CustomerCreate, CustomerUpdate
from ...services import customers as svc

router = APIRouter()


@router.get("/master/customers", dependencies=[Depends(require_roles())])
def list_customers():
    return svc.list_customers()


@router.post("/master/customers", status_code=201, dependencies=[Depends(require_roles("admin", "qm"))])
def create_customer(payload: CustomerCreate):
    return svc.create_customer(payload)


@router.get("/master/customers/{customer_id}", dependencies=[Depends(require_roles())])
def get_customer(customer_id: str):
    return svc.get_customer(customer_id)


@router.put("/master/customers/{customer_id}", dependencies=[Depends(require_roles("admin", "qm"))])
def update_customer(customer_id: str, payload: CustomerUpdate):
    return svc.update_customer(customer_id, payload)
