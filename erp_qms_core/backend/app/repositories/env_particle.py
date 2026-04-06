from __future__ import annotations

from sqlalchemy.orm import Session

from ..models.env_particle import EnvParticleRecord


def count_all(session: Session) -> int:
    return session.query(EnvParticleRecord).filter(EnvParticleRecord.is_deleted == False).count()  # noqa: E712


def list_records(
    session: Session,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 500,
    offset: int = 0,
) -> list[EnvParticleRecord]:
    q = session.query(EnvParticleRecord).filter(EnvParticleRecord.is_deleted == False)  # noqa: E712
    if date_from:
        q = q.filter(EnvParticleRecord.meas_date >= date_from)
    if date_to:
        q = q.filter(EnvParticleRecord.meas_date <= date_to)
    return q.order_by(EnvParticleRecord.meas_date.asc(), EnvParticleRecord.run.asc()).offset(offset).limit(limit).all()


def create_record(session: Session, **kwargs) -> EnvParticleRecord:
    row = EnvParticleRecord(**kwargs)
    session.add(row)
    session.flush()
    return row


def bulk_insert(session: Session, rows: list[dict]) -> int:
    """批次新增，跳過已存在的 (meas_date + run 組合)。回傳實際新增數。"""
    existing = {
        (r.meas_date, r.run)
        for r in session.query(EnvParticleRecord.meas_date, EnvParticleRecord.run)
        .filter(EnvParticleRecord.is_deleted == False)  # noqa: E712
        .all()
    }
    added = 0
    for row in rows:
        key = (row.get("meas_date"), row.get("run"))
        if key in existing:
            continue
        session.add(EnvParticleRecord(**row))
        existing.add(key)
        added += 1
    if added:
        session.flush()
    return added
