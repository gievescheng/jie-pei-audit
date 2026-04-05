from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.db import Base
from .base import TimestampMixin


class CalibrationInstrument(TimestampMixin, Base):
    """量測儀器主檔"""

    __tablename__ = "calibration_instruments"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    instrument_code: Mapped[str] = mapped_column(Text, unique=True, index=True)
    instrument_name: Mapped[str] = mapped_column(Text)
    instrument_type: Mapped[str] = mapped_column(Text, default="")
    model_no: Mapped[str] = mapped_column(Text, default="")
    serial_no: Mapped[str] = mapped_column(Text, default="")
    location: Mapped[str] = mapped_column(Text, default="")
    keeper: Mapped[str] = mapped_column(Text, default="")
    brand: Mapped[str] = mapped_column(Text, default="")
    calib_method: Mapped[str] = mapped_column(Text, default="")  # 外校 / 遊校
    interval_days: Mapped[int] = mapped_column(Integer, default=365)
    needs_msa: Mapped[bool] = mapped_column(default=False)
    status: Mapped[str] = mapped_column(Text, default="active")  # active | retired | exempt

    records: Mapped[list[CalibrationRecord]] = relationship(
        back_populates="instrument", cascade="all, delete-orphan", lazy="selectin"
    )


class CalibrationRecord(TimestampMixin, Base):
    """校正紀錄"""

    __tablename__ = "calibration_records"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    instrument_id: Mapped[str] = mapped_column(
        ForeignKey("calibration_instruments.id", ondelete="CASCADE"), index=True
    )
    calibration_date: Mapped[str] = mapped_column(Text)           # "YYYY-MM-DD"
    next_due_date: Mapped[str | None] = mapped_column(Text, nullable=True)
    result: Mapped[str] = mapped_column(Text, default="合格")      # 合格 | 不合格 | 條件合格
    calibrated_by: Mapped[str] = mapped_column(Text, default="")
    certificate_no: Mapped[str] = mapped_column(Text, default="")
    remarks: Mapped[str] = mapped_column(Text, default="")

    instrument: Mapped[CalibrationInstrument] = relationship(back_populates="records")
