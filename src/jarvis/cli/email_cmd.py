from __future__ import annotations

import argparse

from jarvis.cli.outcome import print_outcome
from jarvis.runtime import app_session
from jarvis.security.gate import PermissionGate
from jarvis.tools.catalog import default_registry


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "email",
        help="Inbox tools. Send always needs confirmation.",
    )
    sub = parser.add_subparsers(dest="email_command", required=True)

    fetch = sub.add_parser("fetch", help="Pull recent messages into the local cache.")
    fetch.add_argument("--limit", type=int, default=20)
    fetch.set_defaults(handler=lambda a: _run("email.fetch", {"limit": a.limit}))

    listed = sub.add_parser("list")
    listed.add_argument("--category", default="")
    listed.set_defaults(
        handler=lambda a: _run("email.list", {"category": a.category or None})
    )

    get_p = sub.add_parser("get")
    get_p.add_argument("id")
    get_p.set_defaults(handler=lambda a: _run("email.get", {"id": a.id}))

    search = sub.add_parser("search")
    search.add_argument("query")
    search.set_defaults(handler=lambda a: _run("email.search", {"query": a.query}))

    classify = sub.add_parser("classify")
    classify.add_argument("id")
    classify.set_defaults(handler=lambda a: _run("email.classify", {"id": a.id}))

    summarize = sub.add_parser("summarize")
    summarize.add_argument("id")
    summarize.set_defaults(handler=lambda a: _run("email.summarize", {"id": a.id}))

    draft = sub.add_parser("draft", help="Save a reply. Does not send.")
    draft.add_argument("id")
    draft.add_argument("--body", default="")
    draft.set_defaults(
        handler=lambda a: _run("email.draft", {"id": a.id, "body": a.body or None})
    )

    send = sub.add_parser("send", help="Send the saved draft (level 2 — confirm).")
    send.add_argument("id")
    send.set_defaults(handler=lambda a: _run("email.send", {"id": a.id}))


def _run(tool: str, payload: dict) -> int:
    with app_session() as (session, _settings):
        outcome = PermissionGate(session, default_registry()).invoke(
            tool, payload, agent="email"
        )
    return print_outcome(outcome)
