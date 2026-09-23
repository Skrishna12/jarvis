"""`jarvis memory` — inspect and change categorized facts."""

from __future__ import annotations

import argparse
import sys

from jarvis.config import load_settings
from jarvis.db.engine import make_engine
from jarvis.db.session import session_scope
from jarvis.memory.categories import MemoryCategory
from jarvis.memory.errors import MemoryError
from jarvis.memory.store import MemoryStore

_CATEGORIES = ", ".join(c.value for c in MemoryCategory)


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "memory",
        help="Store and recall categorized facts.",
    )
    mem_sub = parser.add_subparsers(dest="memory_command", required=True)

    set_p = mem_sub.add_parser("set", help="Create or update a memory.")
    set_p.add_argument("category", help=f"One of: {_CATEGORIES}")
    set_p.add_argument("key")
    set_p.add_argument("value")
    set_p.set_defaults(handler=cmd_set)

    get_p = mem_sub.add_parser("get", help="Print one memory.")
    get_p.add_argument("category", help=f"One of: {_CATEGORIES}")
    get_p.add_argument("key")
    get_p.set_defaults(handler=cmd_get)

    list_p = mem_sub.add_parser("list", help="List keys in a category.")
    list_p.add_argument("category", help=f"One of: {_CATEGORIES}")
    list_p.set_defaults(handler=cmd_list)

    del_p = mem_sub.add_parser("delete", help="Remove one memory.")
    del_p.add_argument("category", help=f"One of: {_CATEGORIES}")
    del_p.add_argument("key")
    del_p.set_defaults(handler=cmd_delete)


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


def cmd_set(args: argparse.Namespace) -> int:
    def inner() -> None:
        with _store_session() as session:
            record = MemoryStore(session).upsert(args.category, args.key, args.value)
        print(f"saved {record.category.value} {record.key}={record.value}")

    return _run(inner)


def cmd_get(args: argparse.Namespace) -> int:
    def inner() -> None:
        with _store_session() as session:
            record = MemoryStore(session).get(args.category, args.key)
        print(f"{record.category.value} {record.key}={record.value}")

    return _run(inner)


def cmd_list(args: argparse.Namespace) -> int:
    def inner() -> None:
        with _store_session() as session:
            records = MemoryStore(session).list(args.category)
        if not records:
            print(f"(no memories in {args.category})")
            return
        for record in records:
            print(f"{record.key}={record.value}")

    return _run(inner)


def cmd_delete(args: argparse.Namespace) -> int:
    def inner() -> None:
        with _store_session() as session:
            record = MemoryStore(session).delete(args.category, args.key)
        print(f"deleted {record.category.value} {record.key}")

    return _run(inner)
