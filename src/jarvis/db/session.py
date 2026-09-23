"""Session helpers: open, commit on success, roll back on failure."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker


def session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)


@contextmanager
def session_scope(engine: Engine) -> Iterator[Session]:
    """Yield a session that commits if the block succeeds.

    On error we roll back and re-raise so the CLI can explain the failure
    instead of leaving a half-written row in SQLite.
    """
    Session = session_factory(engine)
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
