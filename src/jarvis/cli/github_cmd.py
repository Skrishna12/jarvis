from __future__ import annotations

import argparse

from jarvis.cli.outcome import print_outcome
from jarvis.runtime import app_session
from jarvis.security.gate import PermissionGate
from jarvis.tools.catalog import default_registry


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "github",
        help="Read-only GitHub (repos, issues, pulls). Never writes.",
    )
    sub = parser.add_subparsers(dest="github_command", required=True)

    repos = sub.add_parser("repos")
    repos.set_defaults(handler=lambda _a: _run("github.repos", {}))

    issues = sub.add_parser("issues")
    issues.add_argument("repo", help="owner/name")
    issues.set_defaults(handler=lambda a: _run("github.issues", {"repo": a.repo}))

    pulls = sub.add_parser("pulls")
    pulls.add_argument("repo", help="owner/name")
    pulls.set_defaults(handler=lambda a: _run("github.pulls", {"repo": a.repo}))


def _run(tool: str, payload: dict) -> int:
    with app_session() as (session, _settings):
        outcome = PermissionGate(session, default_registry()).invoke(
            tool, payload, agent="github"
        )
    return print_outcome(outcome)
