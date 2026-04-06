from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class EnvParticleRecordCreate(BaseModel):
    meas_date: str              # "YYYY-MM-DD"
    run: int = 1
    session: str = "\u4e0a\u5348"  # 上午
    n_samples: int = 14
    ch1avg: float = 0.0
    ch1max: float = 0.0
    ch2avg: float = 0.0
    ch2max: float = 0.0
    ch3avg: float = 0.0
    ch3max: float = 0.0
    note: str = ""


class EnvParticleBulkSeed(BaseModel):
    records: List[EnvParticleRecordCreate]


class EnvParticleQuery(BaseModel):
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    limit: int = 500
    offset: int = 0
