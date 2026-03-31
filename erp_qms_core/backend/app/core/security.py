from __future__ import annotations

import os
import hashlib
from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# ── 密碼雜湊 ──────────────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    """以 SHA-256 雜湊密碼（MVP 用途；正式環境請改用 bcrypt）。"""
    return hashlib.sha256(plain.encode()).hexdigest()


def verify_password(plain: str, hashed: str) -> bool:
    return hash_password(plain) == hashed


# ── JWT（可選）────────────────────────────────────────────────────────────────
# 若要啟用 JWT，安裝 PyJWT 並設定 ERP_QMS_CORE_JWT_SECRET 環境變數。

def _jwt_secret() -> str:
    secret = os.getenv("ERP_QMS_CORE_JWT_SECRET", "")
    if not secret:
        raise RuntimeError("ERP_QMS_CORE_JWT_SECRET is not set")
    return secret


def create_token(payload: dict) -> str:
    try:
        import jwt as pyjwt
    except ImportError:
        raise RuntimeError("PyJWT not installed; run: pip install PyJWT")
    return pyjwt.encode(payload, _jwt_secret(), algorithm="HS256")


def decode_token(token: str) -> dict | None:
    try:
        import jwt as pyjwt
        return pyjwt.decode(token, _jwt_secret(), algorithms=["HS256"])
    except Exception:
        return None


# ── FastAPI 依賴：RBAC 守門員 ─────────────────────────────────────────────────

_bearer = HTTPBearer(auto_error=False)


def require_roles(*allowed_roles: str) -> Callable:
    """FastAPI 依賴工廠，限制只有特定角色可存取路由。
    使用方式：
        @router.get("/admin", dependencies=[Depends(require_roles("admin", "qms"))])
    """
    def _check(
        credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    ) -> dict:
        if credentials is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="not authenticated")
        payload = decode_token(credentials.credentials)
        if payload is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid or expired token")
        role = payload.get("role", "")
        if allowed_roles and role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="insufficient permissions")
        return payload
    return _check
