from __future__ import annotations

from fastapi import APIRouter

from ...core.responses import ok

router = APIRouter()


@router.get("/health")
def health():
    return ok({"service": "jepe-erp-qms-core"}, message="healthy")
