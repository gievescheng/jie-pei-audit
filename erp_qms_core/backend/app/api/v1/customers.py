from __future__ import annotations

from fastapi import APIRouter

from ...schemas.customers import CustomerCreate, CustomerUpdate
from ...services import customers as svc

router = APIRouter()


@router.get("/master/customers")
def list_customers():
    return svc.list_customers()


@router.post("/master/customers", status_code=201)
def create_customer(payload: CustomerCreate):
    return svc.create_customer(payload)


@router.get("/master/customers/{customer_id}")
def get_customer(customer_id: str):
    return svc.get_customer(customer_id)


@router.put("/master/customers/{customer_id}")
def update_customer(customer_id: str, payload: CustomerUpdate):
    return svc.update_customer(customer_id, payload)
