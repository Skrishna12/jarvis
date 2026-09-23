"""`jarvis conversation` — append and list persisted chat turns."""

from __future__ import annotations

import argparse
import sys

from jarvis.config import load_settings
from jarvis.db.engine import make_engine
from jarvis.db.session import session_scope
from jarvis.memory.conversation import ConversationStore, MessageRole
from jarvis.memory.errors import MemoryError

_ROLES = ", ".join(r.value for r in MessageRole)


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "conversation",
        help="Persist conversation turns (no summarization yet).",
    )
    sub = parser.add_subparsers(dest="conversation_command", required=True)

    add_p = sub.add_parser("add", help="Append one message.")
    add_p.add_argument("role", help=f"One of: {_ROLES}")
    add_p.add_argument("content")
    add_p.set_defaults(handler=cmd_add)

    recent_p = sub.add_parser("recent", help="Show the latest messages, oldest first.")
    recent_p.add_argument("--limit", type=int, default=20)
    recent_p.set_defaults(handler=cmd_recent)


def _store_session():
    settings = load_settings()
    if not settings.database_path.is_file():
        raise MemoryError(
            f"Database file not found: {settings.database_path}. "
            "Run `jarvis db upgrade` first."
        )
    return session_scope(make_engine(settings.database_path))


def _run(fn) -> int:
    try:
        fn()
        return 0
    except MemoryError as exc:
        print(str(exc), file=sys.stderr)
        return 1


def cmd_add(args: argparse.Namespace) -> int:
    def inner() -> None:
        with _store_session() as session:
            record = ConversationStore(session).add(args.role, args.content)
        print(f"{record.role.value}: {record.content}")

    return _run(inner)


def cmd_recent(args: argparse.Namespace) -> int:
    def inner() -> None:
        with _store_session() as session:
            records = ConversationStore(session).recent(limit=args.limit)
        if not records:
            print("(no messages)")
            return
        for record in records:
            print(f"{record.role.value}: {record.content}")

    return _run(inner)
