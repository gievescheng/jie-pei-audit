from __future__ import annotations

from sqlalchemy.orm import Session

from ..models.inventory import Shipment


def list_all(session: Session) -> list[Shipment]:
    return (
        session.query(Shipment)
        .filter(Shipment.is_deleted == False)  # noqa: E712
        .order_by(Shipment.shipment_no.asc())
        .all()
    )


def get_by_id(session: Session, shipment_id: str) -> Shipment | None:
    return (
        session.query(Shipment)
        .filter(Shipment.id == shipment_id, Shipment.is_deleted == False)  # noqa: E712
        .first()
    )


def create(session: Session, **kwargs) -> Shipment:
    row = Shipment(**kwargs)
    session.add(row)
    session.flush()
    return row
