from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.db import Base
from .base import TimestampMixin


class SupplierEvaluation(TimestampMixin, Base):
    """供應商評鑑紀錄（ISO 8.4）"""

    __tablename__ = "supplier_evaluations"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    supplier_id: Mapped[str] = mapped_column(
        ForeignKey("suppliers.id", ondelete="CASCADE"), index=True
    )
    eval_date: Mapped[str] = mapped_column(Text)                    # "YYYY-MM-DD"
    eval_score: Mapped[int] = mapped_column(Integer, default=0)     # 0-100
    eval_result: Mapped[str] = mapped_column(Text, default="合格")  # 優良/合格/條件合格/不合格
    eval_by: Mapped[str] = mapped_column(Text, default="")
    issues: Mapped[str] = mapped_column(Text, default="")           # JSON array stored as text
    remarks: Mapped[str] = mapped_column(Text, default="")
    next_eval_date: Mapped[str | None] = mapped_column(Text, nullable=True)
