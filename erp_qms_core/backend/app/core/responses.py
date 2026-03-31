from __future__ import annotations

import uuid
from typing import Any


def ok(data: Any, message: str = "OK") -> dict:
    return {
        "success": True,
        "data": data,
        "message": message,
        "trace_id": str(uuid.uuid4()),
    }
