"""Open the configured database or explain how to create it."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy.orm import Session

from jarvis.config import Settings, load_settings
from jarvis.db.engine import make_engine
from jarvis.db.session import session_scope


class DatabaseNotReadyError(RuntimeError):
    pass


def load_ready_settings() -> Settings:
    settings = load_settings()
    if not settings.database_path.is_file():
        raise DatabaseNotReadyError(
            f"Database file not found: {settings.database_path}. "
            "Run `jarvis db upgrade` first."
        )
    return settings


@contextmanager
def app_session() -> Iterator[tuple[Session, Settings]]:
    settings = load_ready_settings()
    with session_scope(make_engine(settings.database_path)) as session:
        yield session, settings
