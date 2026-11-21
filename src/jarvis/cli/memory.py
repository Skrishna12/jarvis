"""`jarvis memory` — facts go through the same permission gate as chat tools."""

from __future__ import annotations

import argparse

from jarvis.cli.outcome import print_outcome
from jarvis.memory.categories import MemoryCategory
from jarvis.runtime import app_session
from jarvis.security.gate import PermissionGate
from jarvis.tools.catalog import default_registry

_CATEGORIES = ", ".join(c.value for c in MemoryCategory)


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "memory",
        help="Store and recall categorized facts (gated; delete needs confirmation).",
    )
    mem_sub = parser.add_subparsers(dest="memory_command", required=True)

    set_p = mem_sub.add_parser("set", help="Create or update a memory (level 1).")
    set_p.add_argument("category", help=f"One of: {_CATEGORIES}")
    set_p.add_argument("key")
    set_p.add_argument("value")
    set_p.set_defaults(handler=cmd_set)

    get_p = mem_sub.add_parser("get", help="Print one memory (level 0).")
    get_p.add_argument("category", help=f"One of: {_CATEGORIES}")
    get_p.add_argument("key")
    get_p.set_defaults(handler=cmd_get)

    list_p = mem_sub.add_parser("list", help="List keys in a category (level 0).")
    list_p.add_argument("category", help=f"One of: {_CATEGORIES}")
    list_p.set_defaults(handler=cmd_list)

    del_p = mem_sub.add_parser("delete", help="Remove one memory (level 2 — confirm).")
    del_p.add_argument("category", help=f"One of: {_CATEGORIES}")
    del_p.add_argument("key")
    del_p.set_defaults(handler=cmd_delete)


def _run(tool: str, payload: dict) -> int:
    with app_session() as (session, _settings):
        outcome = PermissionGate(session, default_registry()).invoke(
            tool, payload, agent="memory"
        )
    return print_outcome(outcome)


def cmd_set(args: argparse.Namespace) -> int:
    return _run(
        "memory.upsert",
        {"category": args.category, "key": args.key, "value": args.value},
    )


def cmd_get(args: argparse.Namespace) -> int:
    return _run("memory.get", {"category": args.category, "key": args.key})


def cmd_list(args: argparse.Namespace) -> int:
    return _run("memory.list", {"category": args.category})


def cmd_delete(args: argparse.Namespace) -> int:
    return _run("memory.delete", {"category": args.category, "key": args.key})
