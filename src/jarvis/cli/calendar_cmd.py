from __future__ import annotations

import argparse

from jarvis.cli.outcome import print_outcome
from jarvis.runtime import app_session
from jarvis.security.gate import PermissionGate
from jarvis.tools.catalog import default_registry


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("calendar", help="Local calendar events.")
    sub = parser.add_subparsers(dest="calendar_command", required=True)

    today = sub.add_parser("today")
    today.set_defaults(handler=lambda _a: _run("calendar.today", {}))

    listed = sub.add_parser("list")
    listed.add_argument("--start", default="")
    listed.add_argument("--end", default="")
    listed.set_defaults(
        handler=lambda a: _run(
            "calendar.list",
            {"start": a.start or None, "end": a.end or None},
        )
    )

    create = sub.add_parser("create")
    create.add_argument("title")
    create.add_argument("--start", required=True)
    create.add_argument("--end", default="")
    create.add_argument("--location", default="")
    create.set_defaults(
        handler=lambda a: _run(
            "calendar.create",
            {
                "title": a.title,
                "start_at": a.start,
                "end_at": a.end or None,
                "location": a.location,
            },
        )
    )

    delete = sub.add_parser("delete")
    delete.add_argument("id")
    delete.set_defaults(handler=lambda a: _run("calendar.delete", {"id": a.id}))


def _run(tool: str, payload: dict) -> int:
    with app_session() as (session, _settings):
        outcome = PermissionGate(session, default_registry()).invoke(
            tool, payload, agent="calendar"
        )
    return print_outcome(outcome)
