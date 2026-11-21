from __future__ import annotations

import argparse

from jarvis.cli.outcome import print_outcome
from jarvis.runtime import app_session
from jarvis.security.gate import PermissionGate
from jarvis.tools.catalog import default_registry


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("commute", help="Office hours and traffic headlines.")
    sub = parser.add_subparsers(dest="commute_command", required=True)
    sub.add_parser("status").set_defaults(handler=lambda _a: _run("commute.status", {}))
    sub.add_parser("traffic").set_defaults(handler=lambda _a: _run("commute.traffic", {}))
    city = sub.add_parser("city")
    city.add_argument("name")
    city.set_defaults(handler=lambda a: _run("commute.set_city", {"city": a.name}))
    sub.add_parser("install").set_defaults(handler=lambda _a: _run("commute.install", {}))


def _run(tool: str, payload: dict) -> int:
    with app_session() as (session, _settings):
        outcome = PermissionGate(session, default_registry()).invoke(
            tool, payload, agent="commute"
        )
    return print_outcome(outcome)
