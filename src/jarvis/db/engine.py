"""SQLite engine factory.

The database is a single file on disk. SQLAlchemy talks to it with a URL like
`sqlite:////absolute/path/to/jarvis.db` (four slashes: three for the scheme
plus the leading slash of an absolute path).
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import Engine, create_engine


def sqlite_url(database_path: Path) -> str:
    resolved = database_path.expanduser().resolve()
    return f"sqlite:///{resolved}"


def make_engine(database_path: Path) -> Engine:
    """Create a sync SQLite engine, making the parent folder if needed."""
    database_path = database_path.expanduser()
    database_path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(
        sqlite_url(database_path),
        echo=False,
        # One CLI process, one thread for now. Future workers can revisit this.
        connect_args={"check_same_thread": True},
    )
