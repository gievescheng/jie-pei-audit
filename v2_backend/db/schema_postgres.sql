CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    source_path TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    document_code TEXT NOT NULL DEFAULT '',
    file_type TEXT NOT NULL DEFAULT '',
    version TEXT NOT NULL DEFAULT '',
    owner_dept TEXT NOT NULL DEFAULT '',
    source_system TEXT NOT NULL DEFAULT 'local',
    status TEXT NOT NULL DEFAULT 'active',
    full_text TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS document_chunks (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    page_no INTEGER NULL,
    section_name TEXT NOT NULL DEFAULT '',
    content TEXT NOT NULL,
    embedding vector(1536),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_document_chunk_index UNIQUE (document_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS ix_document_chunks_document_id ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS ix_document_chunks_embedding ON document_chunks USING ivfflat (embedding vector_cosine_ops);

CREATE TABLE IF NOT EXISTS prompt_templates (
    id TEXT PRIMARY KEY,
    template_code TEXT NOT NULL UNIQUE,
    template_name TEXT NOT NULL,
    task_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS prompt_template_versions (
    id TEXT PRIMARY KEY,
    template_id TEXT NOT NULL REFERENCES prompt_templates(id) ON DELETE CASCADE,
    version TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'released',
    system_prompt TEXT NOT NULL,
    policy_prompt TEXT NOT NULL DEFAULT '',
    user_prompt_template TEXT NOT NULL,
    output_schema TEXT NOT NULL DEFAULT '',
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    released_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_prompt_template_version UNIQUE (template_id, version)
);

CREATE TABLE IF NOT EXISTS prompt_template_release_logs (
    id TEXT PRIMARY KEY,
    version_id TEXT NOT NULL REFERENCES prompt_template_versions(id) ON DELETE CASCADE,
    action TEXT NOT NULL,
    note TEXT NOT NULL DEFAULT '',
    actor TEXT NOT NULL DEFAULT 'system',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id TEXT PRIMARY KEY,
    trace_id TEXT NOT NULL,
    task_type TEXT NOT NULL,
    user_id TEXT NOT NULL DEFAULT 'anonymous',
    prompt_version TEXT NOT NULL DEFAULT '',
    result_status TEXT NOT NULL DEFAULT 'success',
    request_summary TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_audit_logs_trace_id ON audit_logs(trace_id);
CREATE INDEX IF NOT EXISTS ix_audit_logs_task_type ON audit_logs(task_type);
