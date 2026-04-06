from __future__ import annotations

from ..core.db import session_scope
from ..repositories import env_particle as repo
from ..schemas.env_particle import EnvParticleRecordCreate, EnvParticleBulkSeed
from ...core.responses import ok


def list_records(
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 500,
    offset: int = 0,
):
    with session_scope() as s:
        rows = repo.list_records(s, date_from=date_from, date_to=date_to, limit=limit, offset=offset)
        total = repo.count_all(s)
        data = [_row_dict(r) for r in rows]
    return ok(data, total=total)


def create_record(payload: EnvParticleRecordCreate):
    with session_scope() as s:
        row = repo.create_record(
            s,
            meas_date=payload.meas_date,
            run=payload.run,
            session=payload.session,
            n_samples=payload.n_samples,
            ch1avg=payload.ch1avg,
            ch1max=payload.ch1max,
            ch2avg=payload.ch2avg,
            ch2max=payload.ch2max,
            ch3avg=payload.ch3avg,
            ch3max=payload.ch3max,
            note=payload.note,
        )
        data = _row_dict(row)
    return ok(data)


def bulk_seed(payload: EnvParticleBulkSeed):
    rows = [r.model_dump() for r in payload.records]
    with session_scope() as s:
        added = repo.bulk_insert(s, rows)
    return ok({"added": added})


def count():
    with session_scope() as s:
        total = repo.count_all(s)
    return ok({"total": total})


def _row_dict(r) -> dict:
    return {
        "id": r.id,
        "meas_date": r.meas_date,
        "run": r.run,
        "session": r.session,
        "N": r.n_samples,
        "ch1avg": r.ch1avg,
        "ch1max": r.ch1max,
        "ch2avg": r.ch2avg,
        "ch2max": r.ch2max,
        "ch3avg": r.ch3avg,
        "ch3max": r.ch3max,
        "note": r.note,
    }
