from __future__ import annotations

import argparse

from jarvis.cli.outcome import print_outcome
from jarvis.runtime import app_session
from jarvis.security.gate import PermissionGate
from jarvis.tools.catalog import default_registry


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("briefing", help="Morning or evening digest.")
    sub = parser.add_subparsers(dest="briefing_command", required=True)
    morning = sub.add_parser("morning")
    morning.set_defaults(handler=lambda _a: _run("briefing.morning", {}))
    evening = sub.add_parser("evening")
    evening.set_defaults(handler=lambda _a: _run("briefing.evening", {}))


def _run(tool: str, payload: dict) -> int:
    with app_session() as (session, _settings):
        outcome = PermissionGate(session, default_registry()).invoke(
            tool, payload, agent="briefing"
        )
    return print_outcome(outcome)
