"""Alembic migrations create the Milestone 2 tables."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import inspect

from jarvis.db.engine import make_engine
from jarvis.db.migrate import current_revision, upgrade_head


def test_upgrade_creates_tables_and_revision(tmp_path: Path) -> None:
    db_path = tmp_path / "migrated.db"
    upgrade_head(db_path)

    assert db_path.is_file()
    assert current_revision(db_path) == "001_m2_memory"

    engine = make_engine(db_path)
    try:
        names = set(inspect(engine).get_table_names())
    finally:
        engine.dispose()

    assert "memories" in names
    assert "conversation_messages" in names
    assert "alembic_version" in names
