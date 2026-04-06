from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.db import Base
from .base import TimestampMixin


class EquipmentMaster(TimestampMixin, Base):
    """設備主檔（ISO 7.1.3）"""

    __tablename__ = "equipment_master"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    equip_no: Mapped[str] = mapped_column(Text, unique=True, index=True)
    equip_name: Mapped[str] = mapped_column(Text)
    location: Mapped[str] = mapped_column(Text, default="")
    model_no: Mapped[str] = mapped_column(Text, default="")
    serial_no: Mapped[str] = mapped_column(Text, default="")
    brand: Mapped[str] = mapped_column(Text, default="")
    interval_days: Mapped[int] = mapped_column(Integer, default=90)
    maint_items: Mapped[str] = mapped_column(Text, default="")   # JSON array stored as text
    status: Mapped[str] = mapped_column(Text, default="active")  # active | retired

    records: Mapped[list[MaintenanceRecord]] = relationship(
        back_populates="equipment", cascade="all, delete-orphan", lazy="selectin",
    )


class MaintenanceRecord(TimestampMixin, Base):
    """保養紀錄"""

    __tablename__ = "maintenance_records"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    equipment_id: Mapped[str] = mapped_column(
        ForeignKey("equipment_master.id", ondelete="CASCADE"), index=True
    )
    maint_date: Mapped[str] = mapped_column(Text)            # "YYYY-MM-DD"
    performed_by: Mapped[str] = mapped_column(Text, default="")
    items_done: Mapped[str] = mapped_column(Text, default="")  # JSON array stored as text
    result: Mapped[str] = mapped_column(Text, default="正常")
    remarks: Mapped[str] = mapped_column(Text, default="")

    equipment: Mapped[EquipmentMaster] = relationship(back_populates="records")
