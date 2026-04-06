from __future__ import annotations

import json

from sqlalchemy.exc import IntegrityError

from ..core.db import session_scope
from ..core.errors import integrity_http_error, not_found_error
from ..core.responses import ok
from ..repositories import equipment as repo
from ..schemas.equipment import (
    EquipmentCreate, EquipmentUpdate,
    MaintenanceRecordCreate, MaintenanceRecordUpdate,
)


def _record_dict(r) -> dict:
    return {
        "id":           r.id,
        "equipment_id": r.equipment_id,
        "maint_date":   r.maint_date,
        "performed_by": r.performed_by,
        "items_done":   _parse_json(r.items_done),
        "result":       r.result,
        "remarks":      r.remarks,
        "created_at":   r.created_at.isoformat() if r.created_at else None,
    }


def _equip_dict(eq) -> dict:
    records = sorted(eq.records, key=lambda r: r.maint_date or "", reverse=True)
    latest = records[0] if records else None
    return {
        "id":              eq.id,
        "equip_no":        eq.equip_no,
        "equip_name":      eq.equip_name,
        "location":        eq.location,
        "model_no":        eq.model_no,
        "serial_no":       eq.serial_no,
        "brand":           eq.brand,
        "interval_days":   eq.interval_days,
        "maint_items":     _parse_json(eq.maint_items),
        "status":          eq.status,
        "last_maint_date": latest.maint_date if latest else None,
        "record_count":    len(records),
    }


def _parse_json(val: str) -> list:
    if not val:
        return []
    try:
        result = json.loads(val)
        return result if isinstance(result, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


# ── Equipment ─────────────────────────────────────────────────────────────────

def list_equipment() -> dict:
    with session_scope() as session:
        rows = repo.list_equipment(session)
        return ok([_equip_dict(r) for r in rows])


def get_equipment(equipment_id: str) -> dict:
    with session_scope() as session:
        row = repo.get_equipment(session, equipment_id)
        if not row:
            raise not_found_error("equipment")
        return ok(_equip_dict(row))


def create_equipment(payload: EquipmentCreate) -> dict:
    try:
        with session_scope() as session:
            row = repo.create_equipment(session, **payload.model_dump())
            return ok({"id": row.id, "equip_no": row.equip_no}, message="created")
    except IntegrityError as exc:
        raise integrity_http_error(exc) from exc


def update_equipment(equipment_id: str, payload: EquipmentUpdate) -> dict:
    with session_scope() as session:
        data = {k: v for k, v in payload.model_dump().items() if v is not None}
        row = repo.update_equipment(session, equipment_id, **data)
        if not row:
            raise not_found_error("equipment")
        return ok(_equip_dict(row), message="updated")


def delete_equipment(equipment_id: str) -> dict:
    with session_scope() as session:
        row = repo.get_equipment(session, equipment_id)
        if not row:
            raise not_found_error("equipment")
        row.is_deleted = True
        return ok({"id": row.id}, message="deleted")


def bulk_seed(items: list[dict]) -> dict:
    created = 0
    with session_scope() as session:
        for item in items:
            equip_no = item.get("equip_no", "")
            if not equip_no:
                continue
            if not repo.get_equipment_by_no(session, equip_no):
                from ..models.equipment import EquipmentMaster
                session.add(EquipmentMaster(**item))
                session.flush()
                created += 1
    return ok({"created": created}, message="bulk_seed done")


# ── Records ───────────────────────────────────────────────────────────────────

def list_records(equipment_id: str | None = None) -> dict:
    with session_scope() as session:
        rows = repo.list_records(session, equipment_id=equipment_id)
        return ok([_record_dict(r) for r in rows])


def create_record(payload: MaintenanceRecordCreate) -> dict:
    try:
        with session_scope() as session:
            row = repo.create_record(session, **payload.model_dump())
            return ok(_record_dict(row), message="created")
    except IntegrityError as exc:
        raise integrity_http_error(exc) from exc


def update_record(record_id: str, payload: MaintenanceRecordUpdate) -> dict:
    with session_scope() as session:
        data = {k: v for k, v in payload.model_dump().items() if v is not None}
        row = repo.update_record(session, record_id, **data)
        if not row:
            raise not_found_error("maintenance_record")
        return ok(_record_dict(row), message="updated")


def delete_record(record_id: str) -> dict:
    with session_scope() as session:
        row = repo.get_record(session, record_id)
        if not row:
            raise not_found_error("maintenance_record")
        row.is_deleted = True
        return ok({"id": row.id}, message="deleted")
