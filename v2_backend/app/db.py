from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import DATA_DIR, settings


SQLITE_FALLBACK_URL = f"sqlite:///{(DATA_DIR / 'v2_dev.db').as_posix()}"
Base = declarative_base()


def _database_mode(url: str) -> str:
    return 'postgresql' if url.startswith('postgresql') else 'sqlite'


def mask_database_url(url: str) -> str:
    if '://' not in url:
        return url
    scheme, rest = url.split('://', 1)
    if '@' not in rest or ':' not in rest.split('@', 1)[0]:
        return url
    credentials, host_part = rest.split('@', 1)
    user = credentials.split(':', 1)[0]
    return f'{scheme}://{user}:***@{host_part}'


def _make_engine(url: str) -> Engine:
    connect_args = {'check_same_thread': False} if url.startswith('sqlite') else {}
    return create_engine(url, future=True, connect_args=connect_args, pool_pre_ping=not url.startswith('sqlite'))


def _probe_engine(engine: Engine, url: str) -> None:
    if url.startswith('sqlite'):
        return
    with engine.connect() as conn:
        conn.execute(text('SELECT 1'))


def _build_engine_state() -> dict:
    configured_url = settings.database_url
    configured_mode = _database_mode(configured_url)
    database_policy = settings.database_policy
    fallback_reason = ''
    try:
        engine = _make_engine(configured_url)
        _probe_engine(engine, configured_url)
        return {
            'engine': engine,
            'active_url': configured_url,
            'active_mode': configured_mode,
            'configured_url': configured_url,
            'configured_mode': configured_mode,
            'database_policy': database_policy,
            'fallback_reason': fallback_reason,
        }
    except Exception as exc:
        fallback_reason = str(exc)
        if database_policy != 'dev':
            raise RuntimeError(
                f"Database connection failed in {database_policy} mode. "
                f"V2 will not silently fall back to SQLite. Reason: {fallback_reason}"
            ) from exc
        fallback_engine = _make_engine(SQLITE_FALLBACK_URL)
        return {
            'engine': fallback_engine,
            'active_url': SQLITE_FALLBACK_URL,
            'active_mode': 'sqlite-fallback',
            'configured_url': configured_url,
            'configured_mode': configured_mode,
            'database_policy': database_policy,
            'fallback_reason': fallback_reason,
        }


ENGINE_STATE = _build_engine_state()
engine = ENGINE_STATE['engine']
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_database_status() -> dict:
    return {
        'configured_database_mode': ENGINE_STATE['configured_mode'],
        'active_database_mode': ENGINE_STATE['active_mode'],
        'database_policy': ENGINE_STATE['database_policy'],
        'configured_database_url': mask_database_url(ENGINE_STATE['configured_url']),
        'active_database_url': mask_database_url(ENGINE_STATE['active_url']),
        'fallback_reason': ENGINE_STATE['fallback_reason'],
        'using_fallback': ENGINE_STATE['active_mode'] != ENGINE_STATE['configured_mode'],
    }


def init_db() -> None:
    from . import models  # noqa: F401

    if settings.database_policy == 'dev':
        Base.metadata.create_all(bind=engine)
        return

    existing_tables = set(inspect(engine).get_table_names())
    required_tables = {
        'documents',
        'document_chunks',
        'prompt_templates',
        'prompt_template_versions',
        'prompt_template_release_logs',
        'audit_logs',
        'compare_cache',
        'audit_cache',
    }
    if not required_tables.issubset(existing_tables):
        missing = ', '.join(sorted(required_tables - existing_tables))
        raise RuntimeError(
            f"V2 database schema is not ready. Missing tables: {missing}. "
            f"Run migrate_v2.py before starting V2 in {settings.database_policy} mode."
        )


@contextmanager
def session_scope():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
