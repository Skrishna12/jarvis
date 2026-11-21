from __future__ import annotations

import argparse

from jarvis.cli.outcome import print_outcome
from jarvis.runtime import app_session
from jarvis.security.gate import PermissionGate
from jarvis.tools.catalog import default_registry


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("project", help="Named projects tasks can attach to.")
    sub = parser.add_subparsers(dest="project_command", required=True)

    listed = sub.add_parser("list")
    listed.add_argument("--status", default="")
    listed.set_defaults(
        handler=lambda a: _run("project.list", {"status": a.status or None})
    )

    create = sub.add_parser("create")
    create.add_argument("name")
    create.add_argument("--description", default="")
    create.set_defaults(
        handler=lambda a: _run(
            "project.create",
            {"name": a.name, "description": a.description},
        )
    )

    update = sub.add_parser("update")
    update.add_argument("id")
    update.add_argument("--status", default="")
    update.add_argument("--description", default="")
    update.set_defaults(
        handler=lambda a: _run(
            "project.update",
            {
                "id": a.id,
                "status": a.status or None,
                "description": a.description or None,
            },
        )
    )


def _run(tool: str, payload: dict) -> int:
    with app_session() as (session, _settings):
        outcome = PermissionGate(session, default_registry()).invoke(
            tool, payload, agent="project"
        )
    return print_outcome(outcome)
