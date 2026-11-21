from __future__ import annotations

import argparse

from jarvis.cli.outcome import print_outcome
from jarvis.runtime import app_session
from jarvis.security.gate import PermissionGate
from jarvis.tools.catalog import default_registry


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("docs", help="Index and search local text files.")
    sub = parser.add_subparsers(dest="docs_command", required=True)

    ingest = sub.add_parser("ingest")
    ingest.add_argument("path")
    ingest.set_defaults(handler=lambda a: _run("docs.ingest", {"path": a.path}))

    search = sub.add_parser("search")
    search.add_argument("query")
    search.set_defaults(handler=lambda a: _run("docs.search", {"query": a.query}))


def _run(tool: str, payload: dict) -> int:
    with app_session() as (session, _settings):
        outcome = PermissionGate(session, default_registry()).invoke(
            tool, payload, agent="docs"
        )
    return print_outcome(outcome)
