from __future__ import annotations

from sqlalchemy.exc import IntegrityError

from ..core.db import session_scope
from ..core.errors import integrity_http_error, not_found_error
from ..core.responses import ok
from ..repositories import bom as repo
from ..schemas.bom import BomItemCreate


def list_bom(product_id: str) -> dict:
    with session_scope() as session:
        if not repo.get_product(session, product_id):
            raise not_found_error("product")
        rows = repo.list_bom(session, product_id)
        return ok([{"id": r.id, "material_id": r.material_id,
                    "qty_per": float(r.qty_per), "loss_rate": float(r.loss_rate)}
                   for r in rows])


def add_bom_item(product_id: str, payload: BomItemCreate) -> dict:
    try:
        with session_scope() as session:
            if not repo.get_product(session, product_id):
                raise not_found_error("product")
            row = repo.create_bom_item(session, product_id, payload.material_id, payload.qty_per, payload.loss_rate)
            return ok({"id": row.id, "product_id": row.product_id,
                       "material_id": row.material_id, "qty_per": float(row.qty_per)}, message="created")
    except IntegrityError as exc:
        raise integrity_http_error(exc) from exc


def delete_bom_item(product_id: str, bom_id: str) -> dict:
    with session_scope() as session:
        row = repo.get_bom_item(session, bom_id, product_id)
        if not row:
            raise not_found_error("bom item")
        row.is_deleted = True
        return ok({"id": bom_id}, message="deleted")
