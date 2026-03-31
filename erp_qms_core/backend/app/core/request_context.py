from __future__ import annotations

import uuid
from contextvars import ContextVar

# 每個 request 的追蹤 ID，可在 middleware 中設定
_trace_id: ContextVar[str] = ContextVar("trace_id", default="")
# 執行此 request 的使用者帳號（未登入時為 "anonymous"）
_actor: ContextVar[str] = ContextVar("actor", default="anonymous")


def set_trace_id(value: str | None = None) -> str:
    tid = value or str(uuid.uuid4())
    _trace_id.set(tid)
    return tid


def get_trace_id() -> str:
    tid = _trace_id.get()
    return tid or set_trace_id()


def set_actor(actor: str) -> None:
    _actor.set(actor or "anonymous")


def get_actor() -> str:
    return _actor.get()
