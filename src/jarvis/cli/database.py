"""`jarvis db` — apply or inspect SQLite migrations."""

from __future__ import annotations

import argparse
import sys

from jarvis.config import load_settings
from jarvis.db.migrate import current_revision, upgrade_head


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("db", help="Create or upgrade the SQLite database.")
    db_sub = parser.add_subparsers(dest="db_command", required=True)
    upgrade = db_sub.add_parser("upgrade", help="Apply migrations (creates the file if needed).")
    upgrade.set_defaults(handler=cmd_upgrade)
    current = db_sub.add_parser("current", help="Print the current Alembic revision.")
    current.set_defaults(handler=cmd_current)


def cmd_upgrade(_args: argparse.Namespace) -> int:
    settings = load_settings()
    try:
        upgrade_head(settings.database_path)
    except OSError as exc:
        print(
            f"Could not create or open the database at {settings.database_path}: {exc}. "
            "Check that JARVIS_DATABASE_PATH is writable.",
            file=sys.stderr,
        )
        return 1
    print(f"Database ready: {settings.database_path}")
    print(f"Revision: {current_revision(settings.database_path)}")
    return 0


def cmd_current(_args: argparse.Namespace) -> int:
    settings = load_settings()
    path = settings.database_path
    if not path.is_file():
        print(
            f"Database file not found: {path}. "
            "Run `jarvis db upgrade` first.",
            file=sys.stderr,
        )
        return 1
    revision = current_revision(path)
    if revision is None:
        print(
            f"No Alembic revision in {path}. "
            "Run `jarvis db upgrade` to apply migrations.",
            file=sys.stderr,
        )
        return 1
    print(revision)
    return 0
