from __future__ import annotations

from ..core.db import session_scope
from ..core.request_context import get_actor, get_trace_id
from ..core.responses import ok
from ..models.audit import AuditLog, ApprovalWorkflow


# ── Audit Log ─────────────────────────────────────────────────────────────────

def write_audit_log(
    module_name: str,
    action: str,
    ref_table: str = "",
    ref_id: str = "",
    summary: str = "",
    actor: str | None = None,
) -> None:
    """記錄一筆操作日誌。在任何 create / update / delete 之後呼叫。"""
    with session_scope() as session:
        session.add(AuditLog(
            trace_id=get_trace_id(),
            module_name=module_name,
            action=action,
            actor=actor or get_actor(),
            ref_table=ref_table,
            ref_id=ref_id,
            summary=summary,
        ))


def list_audit_logs(module_name: str | None = None, limit: int = 100) -> dict:
    with session_scope() as session:
        q = session.query(AuditLog).order_by(AuditLog.created_at.desc())
        if module_name:
            q = q.filter(AuditLog.module_name == module_name)
        rows = q.limit(limit).all()
        return ok([
            {
                "id": r.id,
                "trace_id": r.trace_id,
                "module_name": r.module_name,
                "action": r.action,
                "actor": r.actor,
                "ref_table": r.ref_table,
                "ref_id": r.ref_id,
                "summary": r.summary,
                "created_at": str(r.created_at),
            }
            for r in rows
        ])


# ── Approval Workflow ─────────────────────────────────────────────────────────

def create_approval_step(
    workflow_code: str,
    module_name: str,
    step_name: str,
    ref_id: str = "",
    approver_role_code: str = "",
) -> dict:
    """建立一個審核流程步驟。"""
    with session_scope() as session:
        row = ApprovalWorkflow(
            workflow_code=workflow_code,
            module_name=module_name,
            ref_id=ref_id,
            step_name=step_name,
            approver_role_code=approver_role_code,
            approval_status="pending",
        )
        session.add(row)
        session.flush()
        return ok({
            "id": row.id,
            "workflow_code": row.workflow_code,
            "step_name": row.step_name,
            "approval_status": row.approval_status,
        }, message="created")


def approve_step(step_id: str, actor: str | None = None) -> dict:
    """核准一個審核步驟。"""
    with session_scope() as session:
        row = session.get(ApprovalWorkflow, step_id)
        if not row:
            from ..core.errors import not_found_error
            raise not_found_error("approval step")
        row.approval_status = "approved"
        write_audit_log(
            module_name=row.module_name,
            action="approve",
            ref_table="approval_workflows",
            ref_id=step_id,
            summary=f"step '{row.step_name}' approved",
            actor=actor or get_actor(),
        )
        return ok({"id": row.id, "approval_status": row.approval_status}, message="approved")


def list_pending_steps(module_name: str | None = None) -> dict:
    with session_scope() as session:
        q = session.query(ApprovalWorkflow).filter(ApprovalWorkflow.approval_status == "pending")
        if module_name:
            q = q.filter(ApprovalWorkflow.module_name == module_name)
        rows = q.order_by(ApprovalWorkflow.created_at).all()
        return ok([
            {
                "id": r.id,
                "workflow_code": r.workflow_code,
                "module_name": r.module_name,
                "step_name": r.step_name,
                "approver_role_code": r.approver_role_code,
                "ref_id": r.ref_id,
                "created_at": str(r.created_at),
            }
            for r in rows
        ])
