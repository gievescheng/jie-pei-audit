from __future__ import annotations

from ..core.db import session_scope
from ..core.errors import not_found_error
from ..core.responses import ok
from ..repositories import nonconformance as repo
from ..schemas.nonconformance import NcCreate, NcUpdate, NcBulkSeed


def list_all():
    with session_scope() as s:
        rows = repo.list_all(s)
        data = [_row_dict(r) for r in rows]
    return ok(data)


def create(payload: NcCreate):
    with session_scope() as s:
        row = repo.create(s, **payload.model_dump())
        data = _row_dict(row)
    return ok(data)


def update(nc_no: str, payload: NcUpdate):
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    with session_scope() as s:
        row = repo.update(s, nc_no, **updates)
        if not row:
            raise not_found_error(f"NC {nc_no!r} 不存在")
        data = _row_dict(row)
    return ok(data)


def delete(nc_no: str):
    with session_scope() as s:
        found = repo.soft_delete(s, nc_no)
    if not found:
        raise not_found_error(f"NC {nc_no!r} 不存在")
    return ok(None)


def bulk_seed(payload: NcBulkSeed):
    rows = [r.model_dump() for r in payload.records]
    with session_scope() as s:
        added = repo.bulk_seed(s, rows)
    return ok({"added": added})


def count():
    with session_scope() as s:
        total = repo.count_all(s)
    return ok({"total": total})


def _row_dict(r) -> dict:
    return {
        "id": r.nc_no,           # frontend uses 'id' = nc_no
        "nc_no": r.nc_no,
        "date": r.nc_date,
        "dept": r.dept,
        "type": r.nc_type,
        "description": r.description,
        "severity": r.severity,
        "rootCause": r.root_cause,
        "correctiveAction": r.corrective_action,
        "responsible": r.responsible,
        "dueDate": r.due_date,
        "status": r.status,
        "closeDate": r.close_date,
        "effectiveness": r.effectiveness,
    }
