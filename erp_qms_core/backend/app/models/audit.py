from __future__ import annotations

import uuid

from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from ..core.db import Base
from .base import TimestampMixin


class ApprovalWorkflow(TimestampMixin, Base):
    __tablename__ = "approval_workflows"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_code: Mapped[str] = mapped_column(Text, index=True)
    module_name: Mapped[str] = mapped_column(Text)
    ref_id: Mapped[str] = mapped_column(Text, default="")
    step_name: Mapped[str] = mapped_column(Text)
    approver_role_code: Mapped[str] = mapped_column(Text, default="")
    approval_status: Mapped[str] = mapped_column(Text, default="pending")


class AuditLog(TimestampMixin, Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    trace_id: Mapped[str] = mapped_column(Text, index=True)
    module_name: Mapped[str] = mapped_column(Text, index=True)
    action: Mapped[str] = mapped_column(Text)
    actor: Mapped[str] = mapped_column(Text, default="system")
    ref_table: Mapped[str] = mapped_column(Text, default="")
    ref_id: Mapped[str] = mapped_column(Text, default="")
    summary: Mapped[str] = mapped_column(Text, default="")


class NotificationLog(TimestampMixin, Base):
    __tablename__ = "notification_log"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    channel: Mapped[str] = mapped_column(Text)
    target: Mapped[str] = mapped_column(Text, default="")
    subject: Mapped[str] = mapped_column(Text, default="")
    delivery_status: Mapped[str] = mapped_column(Text, default="pending")
    ref_table: Mapped[str] = mapped_column(Text, default="")
    ref_id: Mapped[str] = mapped_column(Text, default="")
