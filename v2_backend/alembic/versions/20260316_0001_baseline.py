"""v2 baseline schema

Revision ID: 20260316_0001
Revises:
Create Date: 2026-03-16 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260316_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("source_path", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("document_code", sa.Text(), nullable=False, server_default=""),
        sa.Column("file_type", sa.Text(), nullable=False, server_default=""),
        sa.Column("version", sa.Text(), nullable=False, server_default=""),
        sa.Column("owner_dept", sa.Text(), nullable=False, server_default=""),
        sa.Column("source_system", sa.Text(), nullable=False, server_default="local"),
        sa.Column("status", sa.Text(), nullable=False, server_default="active"),
        sa.Column("full_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_documents_source_path", "documents", ["source_path"], unique=True)

    op.create_table(
        "document_chunks",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("document_id", sa.Text(), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("page_no", sa.Integer(), nullable=True),
        sa.Column("section_name", sa.Text(), nullable=False, server_default=""),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("document_id", "chunk_index", name="uq_document_chunk_index"),
    )
    op.create_index("ix_document_chunks_document_id", "document_chunks", ["document_id"], unique=False)

    op.create_table(
        "prompt_templates",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("template_code", sa.Text(), nullable=False),
        sa.Column("template_name", sa.Text(), nullable=False),
        sa.Column("task_type", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_prompt_templates_template_code", "prompt_templates", ["template_code"], unique=True)
    op.create_index("ix_prompt_templates_task_type", "prompt_templates", ["task_type"], unique=False)

    op.create_table(
        "prompt_template_versions",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("template_id", sa.Text(), sa.ForeignKey("prompt_templates.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="released"),
        sa.Column("system_prompt", sa.Text(), nullable=False),
        sa.Column("policy_prompt", sa.Text(), nullable=False, server_default=""),
        sa.Column("user_prompt_template", sa.Text(), nullable=False),
        sa.Column("output_schema", sa.Text(), nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("template_id", "version", name="uq_prompt_template_version"),
    )
    op.create_index("ix_prompt_template_versions_template_id", "prompt_template_versions", ["template_id"], unique=False)
    op.create_index("ix_prompt_template_versions_is_active", "prompt_template_versions", ["is_active"], unique=False)

    op.create_table(
        "prompt_template_release_logs",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("version_id", sa.Text(), sa.ForeignKey("prompt_template_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("note", sa.Text(), nullable=False, server_default=""),
        sa.Column("actor", sa.Text(), nullable=False, server_default="system"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_prompt_template_release_logs_version_id", "prompt_template_release_logs", ["version_id"], unique=False)

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("trace_id", sa.Text(), nullable=False),
        sa.Column("task_type", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Text(), nullable=False, server_default="anonymous"),
        sa.Column("prompt_version", sa.Text(), nullable=False, server_default=""),
        sa.Column("result_status", sa.Text(), nullable=False, server_default="success"),
        sa.Column("request_summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_logs_trace_id", "audit_logs", ["trace_id"], unique=False)
    op.create_index("ix_audit_logs_task_type", "audit_logs", ["task_type"], unique=False)

    op.create_table(
        "compare_cache",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("cache_key", sa.Text(), nullable=False),
        sa.Column("left_document_id", sa.Text(), nullable=False, server_default=""),
        sa.Column("right_document_id", sa.Text(), nullable=False, server_default=""),
        sa.Column("use_llm", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("response_json", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_compare_cache_cache_key", "compare_cache", ["cache_key"], unique=True)
    op.create_index("ix_compare_cache_left_document_id", "compare_cache", ["left_document_id"], unique=False)
    op.create_index("ix_compare_cache_right_document_id", "compare_cache", ["right_document_id"], unique=False)
    op.create_index("ix_compare_cache_use_llm", "compare_cache", ["use_llm"], unique=False)

    op.create_table(
        "audit_cache",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("cache_key", sa.Text(), nullable=False),
        sa.Column("document_id", sa.Text(), nullable=False, server_default=""),
        sa.Column("llm_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("response_json", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_cache_cache_key", "audit_cache", ["cache_key"], unique=True)
    op.create_index("ix_audit_cache_document_id", "audit_cache", ["document_id"], unique=False)
    op.create_index("ix_audit_cache_llm_enabled", "audit_cache", ["llm_enabled"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_audit_cache_llm_enabled", table_name="audit_cache")
    op.drop_index("ix_audit_cache_document_id", table_name="audit_cache")
    op.drop_index("ix_audit_cache_cache_key", table_name="audit_cache")
    op.drop_table("audit_cache")

    op.drop_index("ix_compare_cache_use_llm", table_name="compare_cache")
    op.drop_index("ix_compare_cache_right_document_id", table_name="compare_cache")
    op.drop_index("ix_compare_cache_left_document_id", table_name="compare_cache")
    op.drop_index("ix_compare_cache_cache_key", table_name="compare_cache")
    op.drop_table("compare_cache")

    op.drop_index("ix_audit_logs_task_type", table_name="audit_logs")
    op.drop_index("ix_audit_logs_trace_id", table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index("ix_prompt_template_release_logs_version_id", table_name="prompt_template_release_logs")
    op.drop_table("prompt_template_release_logs")

    op.drop_index("ix_prompt_template_versions_is_active", table_name="prompt_template_versions")
    op.drop_index("ix_prompt_template_versions_template_id", table_name="prompt_template_versions")
    op.drop_table("prompt_template_versions")

    op.drop_index("ix_prompt_templates_task_type", table_name="prompt_templates")
    op.drop_index("ix_prompt_templates_template_code", table_name="prompt_templates")
    op.drop_table("prompt_templates")

    op.drop_index("ix_document_chunks_document_id", table_name="document_chunks")
    op.drop_table("document_chunks")

    op.drop_index("ix_documents_source_path", table_name="documents")
    op.drop_table("documents")
