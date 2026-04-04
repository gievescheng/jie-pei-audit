"""
erp_qms_core/backend/app/core/security.py
密碼雜湊、JWT 簽發 / 驗證、FastAPI RBAC 依賴。
"""
from __future__ import annotations

import datetime
from typing import Callable

import bcrypt
import jwt as pyjwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings


# ── 密碼雜湊（bcrypt）─────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    """bcrypt 雜湊，rounds=12，自動加鹽。"""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """安全比對密碼（常數時間，防 timing attack）。"""
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


# ── JWT 簽發 / 解碼 ───────────────────────────────────────────────────────────

def create_token(payload: dict) -> str:
    """
    簽發 JWT。payload 中的 exp 若未指定，自動加入過期時間。
    呼叫端應在 payload 中提供：
      sub  : str   — user id（UUID）
      role : str   — role_code
      name : str   — 顯示名稱（可選）
    """
    data = dict(payload)
    if "exp" not in data:
        data["exp"] = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
            minutes=settings.token_expire_minutes
        )
    return pyjwt.encode(data, settings.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> dict | None:
    """
    驗證並解碼 JWT。
    回傳 payload dict；若 token 無效或過期，回傳 None。
    """
    try:
        return pyjwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except pyjwt.ExpiredSignatureError:
        return None
    except pyjwt.InvalidTokenError:
        return None


# ── FastAPI 依賴：RBAC 守門員 ─────────────────────────────────────────────────

_bearer = HTTPBearer(auto_error=False)


def require_roles(*allowed_roles: str) -> Callable:
    """
    FastAPI 依賴工廠，限制只有指定角色可存取路由。

    使用方式：
        @router.get("/admin", dependencies=[Depends(require_roles("admin", "qm"))])

    若 allowed_roles 為空，只驗證登入狀態，不限角色。
    """
    def _check(
        credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    ) -> dict:
        if credentials is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="需要登入才能存取此資源。",
                headers={"WWW-Authenticate": "Bearer"},
            )
        payload = decode_token(credentials.credentials)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token 無效或已過期，請重新登入。",
                headers={"WWW-Authenticate": "Bearer"},
            )
        role = payload.get("role", "")
        if allowed_roles and role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"權限不足。此操作需要角色：{', '.join(allowed_roles)}。",
            )
        return payload
    return _check
