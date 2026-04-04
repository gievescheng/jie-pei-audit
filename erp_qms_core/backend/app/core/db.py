from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from .config import settings


Base = declarative_base()

_engine = None
_SessionLocal = None


def _make_engine(url: str):
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    eng = create_engine(
        url,
        future=True,
        connect_args=connect_args,
        pool_pre_ping=not url.startswith("sqlite"),
    )
    if url.startswith("sqlite"):
        @event.listens_for(eng, "connect")
        def _set_sqlite_pragma(dbapi_connection, connection_record):
            del connection_record
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
    return eng


def _get_engine():
    global _engine, _SessionLocal
    if _engine is None:
        _engine = _make_engine(settings.database_url)
        _SessionLocal = sessionmaker(
            bind=_engine, autoflush=False, autocommit=False, future=True
        )
    return _engine, _SessionLocal


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    _, SessionLocal = _get_engine()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_dev_schema() -> None:
    from ..models import master, orders, inventory, audit  # noqa: F401 — registers models

    engine, _ = _get_engine()
    Base.metadata.create_all(bind=engine)

    from .seed import seed_dev
    seed_dev()


def reset_engine() -> None:
    """Force recreation of the engine. Use in tests to pick up a new DB URL."""
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None
