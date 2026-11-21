from __future__ import annotations

import argparse

from jarvis.cli.outcome import print_outcome
from jarvis.runtime import app_session
from jarvis.security.gate import PermissionGate
from jarvis.tools.catalog import default_registry


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("notify", help="Unread in-app notifications.")
    sub = parser.add_subparsers(dest="notify_command", required=True)

    listed = sub.add_parser("list")
    listed.set_defaults(handler=lambda _a: _run("notify.list", {}))

    read = sub.add_parser("read")
    read.add_argument("id")
    read.set_defaults(handler=lambda a: _run("notify.read", {"id": a.id}))


def _run(tool: str, payload: dict) -> int:
    with app_session() as (session, _settings):
        outcome = PermissionGate(session, default_registry()).invoke(
            tool, payload, agent="notify"
        )
    return print_outcome(outcome)
