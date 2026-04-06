from __future__ import annotations

import uuid

from sqlalchemy import Float, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..core.db import Base
from .base import TimestampMixin


class EnvParticleRecord(TimestampMixin, Base):
    """環境粒子計數量測紀錄"""

    __tablename__ = "env_particle_records"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    meas_date: Mapped[str] = mapped_column(Text, index=True)   # "YYYY-MM-DD"
    run: Mapped[int] = mapped_column(Integer, default=1)        # 當日第幾筆
    session: Mapped[str] = mapped_column(Text, default="上午")  # 上午 / 下午
    n_samples: Mapped[int] = mapped_column(Integer, default=14) # 量測次數 N
    ch1avg: Mapped[float] = mapped_column(Float, default=0.0)
    ch1max: Mapped[float] = mapped_column(Float, default=0.0)
    ch2avg: Mapped[float] = mapped_column(Float, default=0.0)
    ch2max: Mapped[float] = mapped_column(Float, default=0.0)
    ch3avg: Mapped[float] = mapped_column(Float, default=0.0)
    ch3max: Mapped[float] = mapped_column(Float, default=0.0)
    note: Mapped[str] = mapped_column(Text, default="")
