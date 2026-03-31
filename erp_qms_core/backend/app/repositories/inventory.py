from __future__ import annotations

from sqlalchemy.orm import Session

from ..models.inventory import InventoryLocation, InventoryTransaction


def list_locations(session: Session) -> list[InventoryLocation]:
    return (
        session.query(InventoryLocation)
        .filter(InventoryLocation.is_deleted == False)  # noqa: E712
        .order_by(InventoryLocation.location_code.asc())
        .all()
    )


def create_location(session: Session, **kwargs) -> InventoryLocation:
    row = InventoryLocation(**kwargs)
    session.add(row)
    session.flush()
    return row


def list_transactions(session: Session, limit: int = 200) -> list[InventoryTransaction]:
    return (
        session.query(InventoryTransaction)
        .order_by(InventoryTransaction.trx_date.desc())
        .limit(limit)
        .all()
    )


def create_transaction(session: Session, **kwargs) -> InventoryTransaction:
    row = InventoryTransaction(**kwargs)
    session.add(row)
    session.flush()
    return row
