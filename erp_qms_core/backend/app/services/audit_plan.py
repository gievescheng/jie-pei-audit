from __future__ import annotations

from ..core.db import session_scope
from ..core.errors import not_found_error
from ..core.responses import ok
from ..repositories import audit_plan as repo
from ..schemas.audit_plan import AuditPlanCreate, AuditPlanUpdate, AuditPlanBulkSeed


def list_all():
    with session_scope() as s:
        rows = repo.list_all(s)
        data = [_row_dict(r) for r in rows]
    return ok(data)


def create(payload: AuditPlanCreate):
    with session_scope() as s:
        row = repo.create(s, **payload.model_dump())
        data = _row_dict(row)
    return ok(data)


def update(plan_no: str, payload: AuditPlanUpdate):
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    with session_scope() as s:
        row = repo.update(s, plan_no, **updates)
        if not row:
            raise not_found_error(f"稽核計畫 {plan_no!r} 不存在")
        data = _row_dict(row)
    return ok(data)


def delete(plan_no: str):
    with session_scope() as s:
        found = repo.soft_delete(s, plan_no)
    if not found:
        raise not_found_error(f"稽核計畫 {plan_no!r} 不存在")
    return ok(None)


def bulk_seed(payload: AuditPlanBulkSeed):
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
        "id": r.plan_no,        # frontend uses 'id' = plan_no
        "plan_no": r.plan_no,
        "year": r.year,
        "period": r.period,
        "scheduledDate": r.scheduled_date,
        "dept": r.dept,
        "scope": r.scope,
        "auditor": r.auditor,
        "auditee": r.auditee,
        "status": r.status,
        "actualDate": r.actual_date,
        "findings": r.findings,
        "ncCount": r.nc_count,
    }
