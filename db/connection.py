"""Shared database engine with a resilient embedded fallback."""

import logging
import os
import threading
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


load_dotenv()
logger = logging.getLogger(__name__)

_engine: Engine | None = None
_backend: str | None = None
_engine_lock = threading.Lock()


SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS posts (
    postid INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT UNIQUE,
    tickers TEXT,
    positive FLOAT,
    negative FLOAT,
    neutral FLOAT,
    confidence FLOAT,
    post_text TEXT,
    score FLOAT,
    upvote_ratio FLOAT,
    creation DATE
)
"""


def _primary_engine(connection_string: str) -> Engine:
    normalized = connection_string
    if normalized.startswith("postgres://"):
        normalized = normalized.replace("postgres://", "postgresql://", 1)
    return create_engine(
        normalized,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 5},
    )


def _sqlite_engine() -> Engine:
    configured_path = os.getenv("SQLITE_FALLBACK_PATH", "/tmp/marketsent.db")
    database_path = Path(configured_path).expanduser().resolve()
    database_path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(
        f"sqlite:///{database_path}",
        connect_args={"check_same_thread": False, "timeout": 30},
    )


def _verify(engine: Engine) -> None:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))


def _initialize_sqlite(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(text(SQLITE_SCHEMA))
        connection.execute(
            text("CREATE INDEX IF NOT EXISTS post_day_created ON posts(creation)")
        )


def get_engine() -> Engine:
    """Return PostgreSQL when healthy, otherwise a local SQLite continuity store."""

    global _engine, _backend
    if _engine is not None:
        return _engine

    with _engine_lock:
        if _engine is not None:
            return _engine

        connection_string = os.getenv("DB_CONNECTION_STRING", "").strip()
        if connection_string:
            candidate = _primary_engine(connection_string)
            try:
                _verify(candidate)
            except Exception as error:
                candidate.dispose()
                logger.warning(
                    "PostgreSQL is unavailable; using the SQLite continuity store: %s",
                    error,
                )
            else:
                _engine = candidate
                _backend = "postgresql"
                return _engine

        fallback = _sqlite_engine()
        _initialize_sqlite(fallback)
        _engine = fallback
        _backend = "sqlite"
        return _engine


def get_backend() -> str:
    """Return the active storage backend name."""

    get_engine()
    return _backend or "unknown"


def reset_engine() -> None:
    """Dispose cached state, primarily for isolated tests."""

    global _engine, _backend
    with _engine_lock:
        if _engine is not None:
            _engine.dispose()
        _engine = None
        _backend = None
