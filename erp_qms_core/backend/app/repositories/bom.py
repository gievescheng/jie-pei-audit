from __future__ import annotations

from sqlalchemy.orm import Session

from ..models.master import BomItem, Product


def get_product(session: Session, product_id: str) -> Product | None:
    return session.query(Product).filter(Product.id == product_id).first()


def list_bom(session: Session, product_id: str) -> list[BomItem]:
    return (
        session.query(BomItem)
        .filter(BomItem.product_id == product_id, BomItem.is_deleted == False)  # noqa: E712
        .all()
    )


def get_bom_item(session: Session, bom_id: str, product_id: str) -> BomItem | None:
    return (
        session.query(BomItem)
        .filter(BomItem.id == bom_id, BomItem.product_id == product_id)
        .first()
    )


def create_bom_item(
    session: Session,
    product_id: str,
    material_id: str,
    qty_per: float,
    loss_rate: float,
) -> BomItem:
    row = BomItem(product_id=product_id, material_id=material_id, qty_per=qty_per, loss_rate=loss_rate)
    session.add(row)
    session.flush()
    return row
