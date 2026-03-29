"""
auth.py — 登入與權限管理的加密核心模組

包含：
- 密碼雜湊與驗證
- JWT 通行證的製作與驗證
- Refresh Token（更新通行證）的製作
- 從 HTTP Header 取出通行證
- 驗證目前使用者身份
- 驗證使用者是否有特定權限
"""
from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt as _bcrypt

from fastapi import HTTPException
from jose import JWTError, jwt

from .config import settings
from .db import session_scope
from . import models

# ── 密碼加密設定 ──────────────────────────────────────────
# 登入驗證時，若查無此人也要跑一次 verify 防止計時攻擊
# （這個 hash 是 "dummy" 密碼的 bcrypt 結果，僅用來填時間）
_DUMMY_HASH = b"$2b$12$KIXCBWWfGMrmNe7iMYBOneOzRdAiefnSzZpxq7i3GF.xiqPQqjg4i"


def hash_password(plain: str) -> str:
    """把明文密碼轉成 bcrypt 雜湊值，存入資料庫。"""
    return _bcrypt.hashpw(plain.encode(), _bcrypt.gensalt(rounds=12)).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """驗證明文密碼是否符合已雜湊的密碼。"""
    try:
        return _bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


# ── 通行證（JWT）製作 ─────────────────────────────────────

def create_access_token(payload: dict, expires_minutes: int = 30) -> str:
    """
    製作 Access Token（短效通行證，預設 30 分鐘到期）。
    payload 必須包含 {"sub": user.id, "emp_no": ..., "role_id": ...}。
    """
    now = datetime.now(timezone.utc)
    to_encode = {
        **payload,
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
        "jti": str(uuid.uuid4()),  # 每張通行證獨一無二的編號
    }
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: str) -> tuple[str, str]:
    """
    製作 Refresh Token（長效更新通行證，7 天到期）。
    回傳 (明文 token, SHA-256 雜湊值)。
    明文只回傳給使用者一次；資料庫只存雜湊值。
    """
    raw = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(raw.encode()).hexdigest()
    return raw, token_hash


def decode_token(token: str) -> dict:
    """
    解碼並驗證 JWT 通行證。
    若通行證無效或已過期，回傳 HTTP 401 錯誤。
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"verify_exp": True},
        )
        return payload
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="通行證無效或已過期") from exc


def extract_bearer(authorization: str | None) -> str:
    """
    從 HTTP Authorization Header 取出 Bearer Token。
    例如：Authorization: Bearer eyJhbGci...
    若格式不對，回傳 HTTP 401 錯誤。
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="缺少或格式錯誤的 Authorization Header")
    return authorization.removeprefix("Bearer ").strip()


def get_current_user(token: str) -> models.User:
    """
    根據通行證查詢目前登入的使用者。
    若使用者不存在或已停用，回傳 HTTP 401 錯誤。
    """
    payload = decode_token(token)
    user_id: str | None = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="通行證缺少使用者識別碼")
    with session_scope() as session:
        user = (
            session.query(models.User)
            .filter(models.User.id == user_id, models.User.is_active == True)
            .first()
        )
        if user is None:
            raise HTTPException(status_code=401, detail="使用者不存在或已停用")
        # 在 session 關閉前把需要的屬性讀出來（避免 lazy load 問題）
        # 回傳一個帶有必要屬性的簡易物件
        return _detach_user(user)


def require_permission(token: str, permission_code: str) -> models.User:
    """
    驗證通行證，並確認使用者擁有指定權限。
    若無此權限，回傳 HTTP 403 錯誤。
    回傳使用者物件，讓呼叫端可以記錄「是誰做了這件事」。
    """
    user = get_current_user(token)
    if not user.role_id:
        raise HTTPException(status_code=403, detail="此帳號尚未指派角色")
    with session_scope() as session:
        perm = (
            session.query(models.RolePermission)
            .filter(
                models.RolePermission.role_id == user.role_id,
                models.RolePermission.permission_code == permission_code,
                models.RolePermission.is_deleted == False,
            )
            .first()
        )
        if perm is None:
            raise HTTPException(
                status_code=403,
                detail=f"權限不足，需要 '{permission_code}' 權限",
            )
    return user


# ── 服務間內部金鑰驗證 ───────────────────────────────────

def require_service_key(x_service_key: str | None) -> None:
    """
    驗證服務間呼叫的內部金鑰（X-Service-Key Header）。
    僅供 v2_backend 等內部服務使用，不開放給一般使用者。
    金鑰不符時回傳 HTTP 401。
    """
    import secrets as _secrets
    expected = settings.internal_service_key
    if not x_service_key or not _secrets.compare_digest(x_service_key, expected):
        raise HTTPException(status_code=401, detail="內部服務金鑰無效")


# ── 內部工具 ──────────────────────────────────────────────

class _UserSnapshot:
    """User 物件的簡易快照，避免 session 關閉後的 lazy load 問題。"""
    __slots__ = ("id", "emp_no", "name", "email", "dept_id", "role_id", "is_active")

    def __init__(self, user: models.User) -> None:
        self.id = user.id
        self.emp_no = user.emp_no
        self.name = user.name
        self.email = user.email
        self.dept_id = user.dept_id
        self.role_id = user.role_id
        self.is_active = user.is_active


def _detach_user(user: models.User) -> _UserSnapshot:
    return _UserSnapshot(user)
