from __future__ import annotations

import uuid

from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from ..core.db import Base
from .base import TimestampMixin


class NonConformance(TimestampMixin, Base):
    """不符合報告（NC）"""

    __tablename__ = "non_conformances"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    nc_no: Mapped[str] = mapped_column(Text, unique=True, index=True)   # NC-2025-001
    nc_date: Mapped[str] = mapped_column(Text, default="")               # YYYY-MM-DD
    dept: Mapped[str] = mapped_column(Text, default="")
    nc_type: Mapped[str] = mapped_column(Text, default="\u88fd\u7a0b\u7570\u5e38")  # 製程異常
    description: Mapped[str] = mapped_column(Text, default="")
    severity: Mapped[str] = mapped_column(Text, default="\u8f15\u5fae")  # 輕微
    root_cause: Mapped[str] = mapped_column(Text, default="")
    corrective_action: Mapped[str] = mapped_column(Text, default="")
    responsible: Mapped[str] = mapped_column(Text, default="")
    due_date: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(Text, default="\u5f85\u8655\u7406")  # 待處理
    close_date: Mapped[str] = mapped_column(Text, default="")
    effectiveness: Mapped[str] = mapped_column(Text, default="")
