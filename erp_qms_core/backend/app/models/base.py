from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..core.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    created_by: Mapped[str] = mapped_column(Text, default="system")
    updated_by: Mapped[str] = mapped_column(Text, default="system")
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
