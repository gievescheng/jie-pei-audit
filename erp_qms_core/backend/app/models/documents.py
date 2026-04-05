from __future__ import annotations

import uuid

from sqlalchemy import Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..core.db import Base
from .base import TimestampMixin


class QmsDocument(TimestampMixin, Base):
    """QMS 文件版本主檔（ISO 7.5）"""

    __tablename__ = "qms_documents"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    doc_no: Mapped[str] = mapped_column(Text, unique=True, index=True)       # 文件編號
    doc_name: Mapped[str] = mapped_column(Text)                               # 文件名稱
    doc_type: Mapped[str] = mapped_column(Text, default="管理程序")           # 管理手冊/管理程序/作業指導書/表單
    version: Mapped[str] = mapped_column(Text, default="1.0")
    department: Mapped[str] = mapped_column(Text, default="")
    author: Mapped[str] = mapped_column(Text, default="")
    issue_date: Mapped[str] = mapped_column(Text, default="")                 # "YYYY-MM-DD"
    retention_years: Mapped[int] = mapped_column(Integer, default=16)
    pdf_path: Mapped[str] = mapped_column(Text, default="")                   # 相對路徑
    docx_path: Mapped[str] = mapped_column(Text, default="")
    remarks: Mapped[str] = mapped_column(Text, default="")
