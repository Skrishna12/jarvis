"""Run Alembic migrations against a chosen SQLite file."""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config

from jarvis.config import PROJECT_ROOT
from jarvis.db.engine import sqlite_url

_ALEMBIC_INI = PROJECT_ROOT / "alembic.ini"


def alembic_config(database_path: Path) -> Config:
    if not _ALEMBIC_INI.is_file():
        raise FileNotFoundError(
            f"Could not find {_ALEMBIC_INI}. Run commands from a clone of "
            "this repo so Alembic can find alembic.ini."
        )
    cfg = Config(str(_ALEMBIC_INI))
    cfg.set_main_option("sqlalchemy.url", sqlite_url(database_path))
    return cfg


def upgrade_head(database_path: Path) -> None:
    """Apply all migrations (creates the file and tables if needed)."""
    database_path.parent.mkdir(parents=True, exist_ok=True)
    command.upgrade(alembic_config(database_path), "head")


def current_revision(database_path: Path) -> str | None:
    """Return the database's Alembic revision, or None if uninitialized."""
    from alembic.runtime.migration import MigrationContext
    from sqlalchemy import create_engine

    if not database_path.is_file():
        return None
    engine = create_engine(sqlite_url(database_path))
    try:
        with engine.connect() as conn:
            context = MigrationContext.configure(conn)
            return context.get_current_revision()
    finally:
        engine.dispose()
