from __future__ import annotations

import json
from datetime import date, timedelta

from sqlalchemy.exc import IntegrityError

from ..core.db import session_scope
from ..core.errors import integrity_http_error, not_found_error
from ..core.responses import ok
from ..repositories import supplier_eval as repo
from ..schemas.supplier_eval import SupplierEvaluationCreate, SupplierEvaluationUpdate


def _eval_dict(e) -> dict:
    return {
        "id":             e.id,
        "supplier_id":    e.supplier_id,
        "eval_date":      e.eval_date,
        "eval_score":     e.eval_score,
        "eval_result":    e.eval_result,
        "eval_by":        e.eval_by,
        "issues":         _parse_json(e.issues),
        "remarks":        e.remarks,
        "next_eval_date": e.next_eval_date,
        "created_at":     e.created_at.isoformat() if e.created_at else None,
    }


def _parse_json(val: str) -> list:
    if not val:
        return []
    try:
        result = json.loads(val)
        return result if isinstance(result, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def list_evaluations(supplier_id: str | None = None) -> dict:
    with session_scope() as session:
        rows = repo.list_evaluations(session, supplier_id=supplier_id)
        return ok([_eval_dict(r) for r in rows])


def get_evaluation(eval_id: str) -> dict:
    with session_scope() as session:
        row = repo.get_evaluation(session, eval_id)
        if not row:
            raise not_found_error("supplier_evaluation")
        return ok(_eval_dict(row))


def create_evaluation(payload: SupplierEvaluationCreate) -> dict:
    try:
        with session_scope() as session:
            data = payload.model_dump()
            # 自動計算下次評鑑日（若未指定，預設 365 天後）
            if not data.get("next_eval_date") and data.get("eval_date"):
                try:
                    d = date.fromisoformat(data["eval_date"])
                    data["next_eval_date"] = (d + timedelta(days=365)).isoformat()
                except ValueError:
                    pass
            row = repo.create_evaluation(session, **data)
            return ok(_eval_dict(row), message="created")
    except IntegrityError as exc:
        raise integrity_http_error(exc) from exc


def update_evaluation(eval_id: str, payload: SupplierEvaluationUpdate) -> dict:
    with session_scope() as session:
        data = {k: v for k, v in payload.model_dump().items() if v is not None}
        row = repo.update_evaluation(session, eval_id, **data)
        if not row:
            raise not_found_error("supplier_evaluation")
        return ok(_eval_dict(row), message="updated")


def delete_evaluation(eval_id: str) -> dict:
    with session_scope() as session:
        row = repo.get_evaluation(session, eval_id)
        if not row:
            raise not_found_error("supplier_evaluation")
        row.is_deleted = True
        return ok({"id": row.id}, message="deleted")
