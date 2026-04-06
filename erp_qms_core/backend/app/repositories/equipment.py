from __future__ import annotations
from sqlalchemy.orm import Session
from ..models.equipment import EquipmentMaster, MaintenanceRecord


def list_equipment(session: Session) -> list[EquipmentMaster]:
    return (
        session.query(EquipmentMaster)
        .filter(EquipmentMaster.is_deleted == False)  # noqa: E712
        .order_by(EquipmentMaster.equip_no.asc())
        .all()
    )


def get_equipment(session: Session, equipment_id: str) -> EquipmentMaster | None:
    return (
        session.query(EquipmentMaster)
        .filter(EquipmentMaster.id == equipment_id, EquipmentMaster.is_deleted == False)  # noqa: E712
        .first()
    )


def get_equipment_by_no(session: Session, equip_no: str) -> EquipmentMaster | None:
    return (
        session.query(EquipmentMaster)
        .filter(EquipmentMaster.equip_no == equip_no, EquipmentMaster.is_deleted == False)  # noqa: E712
        .first()
    )


def create_equipment(session: Session, **kwargs) -> EquipmentMaster:
    row = EquipmentMaster(**kwargs)
    session.add(row)
    session.flush()
    return row


def update_equipment(session: Session, equipment_id: str, **kwargs) -> EquipmentMaster | None:
    row = get_equipment(session, equipment_id)
    if not row:
        return None
    for k, v in kwargs.items():
        if v is not None:
            setattr(row, k, v)
    session.flush()
    return row


def list_records(session: Session, equipment_id: str | None = None) -> list[MaintenanceRecord]:
    q = session.query(MaintenanceRecord).filter(MaintenanceRecord.is_deleted == False)  # noqa: E712
    if equipment_id:
        q = q.filter(MaintenanceRecord.equipment_id == equipment_id)
    return q.order_by(MaintenanceRecord.maint_date.desc()).all()


def get_record(session: Session, record_id: str) -> MaintenanceRecord | None:
    return (
        session.query(MaintenanceRecord)
        .filter(MaintenanceRecord.id == record_id, MaintenanceRecord.is_deleted == False)  # noqa: E712
        .first()
    )


def create_record(session: Session, **kwargs) -> MaintenanceRecord:
    row = MaintenanceRecord(**kwargs)
    session.add(row)
    session.flush()
    return row


def update_record(session: Session, record_id: str, **kwargs) -> MaintenanceRecord | None:
    row = get_record(session, record_id)
    if not row:
        return None
    for k, v in kwargs.items():
        if v is not None:
            setattr(row, k, v)
    session.flush()
    return row
