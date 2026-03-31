from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError


def integrity_http_error(exc: IntegrityError) -> HTTPException:
    detail = str(getattr(exc, "orig", exc)).lower()
    if "unique constraint" in detail or "duplicate key value" in detail:
        return HTTPException(status_code=409, detail="resource already exists")
    if "foreign key constraint" in detail or "violates foreign key constraint" in detail:
        return HTTPException(status_code=422, detail="related resource does not exist")
    return HTTPException(status_code=400, detail="invalid database write")


def not_found_error(resource: str) -> HTTPException:
    return HTTPException(status_code=404, detail=f"{resource} not found")
