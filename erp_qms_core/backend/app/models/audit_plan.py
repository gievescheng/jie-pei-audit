from __future__ import annotations

import uuid

from sqlalchemy import Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..core.db import Base
from .base import TimestampMixin


class AuditPlan(TimestampMixin, Base):
    """內部稽核計畫"""

    __tablename__ = "audit_plans"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    plan_no: Mapped[str] = mapped_column(Text, unique=True, index=True)  # IA-2025-01
    year: Mapped[int] = mapped_column(Integer, default=0)
    period: Mapped[str] = mapped_column(Text, default="")                 # 上半年 / 下半年
    scheduled_date: Mapped[str] = mapped_column(Text, default="")         # YYYY-MM-DD
    dept: Mapped[str] = mapped_column(Text, default="")
    scope: Mapped[str] = mapped_column(Text, default="")                  # 逗號分隔程序代號
    auditor: Mapped[str] = mapped_column(Text, default="")
    auditee: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(Text, default="\u8a08\u756b\u4e2d")  # 計畫中
    actual_date: Mapped[str] = mapped_column(Text, default="")
    findings: Mapped[int] = mapped_column(Integer, default=0)
    nc_count: Mapped[int] = mapped_column(Integer, default=0)
