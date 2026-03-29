from __future__ import annotations

from .repositories import create_audit_log


def write_audit_log(session, *, trace_id: str, task_type: str, prompt_version: str, result_status: str, request_summary: str, user_id: str = "anonymous"):
    return create_audit_log(
        session,
        trace_id=trace_id,
        task_type=task_type,
        user_id=user_id,
        prompt_version=prompt_version,
        result_status=result_status,
        request_summary=request_summary,
    )
