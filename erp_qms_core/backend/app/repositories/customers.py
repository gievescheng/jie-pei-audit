from __future__ import annotations

from sqlalchemy.orm import Session

from ..models.master import Customer


def list_all(session: Session) -> list[Customer]:
    return (
        session.query(Customer)
        .filter(Customer.is_deleted == False)  # noqa: E712
        .order_by(Customer.customer_code.asc())
        .all()
    )


def get_by_id(session: Session, customer_id: str) -> Customer | None:
    return (
        session.query(Customer)
        .filter(Customer.id == customer_id, Customer.is_deleted == False)  # noqa: E712
        .first()
    )


def create(session: Session, customer_code: str, customer_name: str, short_name: str = "") -> Customer:
    row = Customer(customer_code=customer_code, customer_name=customer_name, short_name=short_name)
    session.add(row)
    session.flush()
    return row
