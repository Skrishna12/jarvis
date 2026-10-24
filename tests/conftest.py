"""Shared fixtures: a throwaway SQLite database per test."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy.orm import Session, sessionmaker

from jarvis.db.engine import make_engine
from jarvis.db.models import Base


@pytest.fixture
def db_session(tmp_path: Path) -> Iterator[Session]:
    engine = make_engine(tmp_path / "test.db")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    session = factory()
    try:
        yield session
        session.commit()
    finally:
        session.close()
        engine.dispose()
