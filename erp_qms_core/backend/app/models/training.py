from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.db import Base
from .base import TimestampMixin


class TrainingEmployee(TimestampMixin, Base):
    """員工主檔（訓練管理用，ISO 7.2）"""

    __tablename__ = "training_employees"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    emp_no: Mapped[str] = mapped_column(Text, unique=True, index=True)   # 員工編號
    emp_name: Mapped[str] = mapped_column(Text)
    department: Mapped[str] = mapped_column(Text, default="")
    role: Mapped[str] = mapped_column(Text, default="")
    hire_date: Mapped[str] = mapped_column(Text, default="")             # "YYYY-MM-DD"
    status: Mapped[str] = mapped_column(Text, default="active")          # active | resigned

    records: Mapped[list[TrainingRecord]] = relationship(
        back_populates="employee", cascade="all, delete-orphan", lazy="selectin"
    )


class TrainingRecord(TimestampMixin, Base):
    """訓練紀錄"""

    __tablename__ = "training_records"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    employee_id: Mapped[str] = mapped_column(
        ForeignKey("training_employees.id", ondelete="CASCADE"), index=True
    )
    course_name: Mapped[str] = mapped_column(Text)
    training_date: Mapped[str] = mapped_column(Text, default="")        # "YYYY-MM-DD"
    training_type: Mapped[str] = mapped_column(Text, default="內訓")    # 內訓 | 外訓
    result: Mapped[str] = mapped_column(Text, default="合格")            # 合格 | 不合格
    certificate_no: Mapped[str] = mapped_column(Text, default="無")
    validity_months: Mapped[int] = mapped_column(Integer, default=0)    # 0 = 永久有效
    remarks: Mapped[str] = mapped_column(Text, default="")

    employee: Mapped[TrainingEmployee] = relationship(back_populates="records")
