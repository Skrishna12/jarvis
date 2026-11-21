from __future__ import annotations

import argparse

from jarvis.cli.outcome import print_outcome
from jarvis.runtime import app_session
from jarvis.security.gate import PermissionGate
from jarvis.tools.catalog import default_registry


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "news",
        help="National and international headlines (public RSS, no extra key).",
    )
    parser.set_defaults(handler=lambda _a: _run({}))


def _run(payload: dict) -> int:
    with app_session() as (session, _settings):
        outcome = PermissionGate(session, default_registry()).invoke(
            "news.digest", payload, agent="news"
        )
    return print_outcome(outcome)
