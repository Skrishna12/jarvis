from __future__ import annotations

import argparse

from jarvis.cli.outcome import print_outcome
from jarvis.runtime import app_session
from jarvis.security.gate import PermissionGate
from jarvis.tools.catalog import default_registry


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "reminder", help="Reminder tools (go through the permission gate)."
    )
    sub = parser.add_subparsers(dest="reminder_command", required=True)

    listed = sub.add_parser("list")
    listed.set_defaults(handler=lambda _a: _run("reminder.list", {}))

    due = sub.add_parser("due")
    due.set_defaults(handler=lambda _a: _run("reminder.due", {}))

    create = sub.add_parser("create")
    create.add_argument("title")
    create.add_argument("--at", dest="trigger_at", required=True, help="ISO datetime")
    create.add_argument("--kind", default="one_time")
    create.add_argument("--recurrence", default="")
    create.add_argument("--message", default="")
    create.add_argument("--task-id", dest="task_id", default="")
    create.set_defaults(
        handler=lambda a: _run(
            "reminder.create",
            {
                "title": a.title,
                "trigger_at": a.trigger_at,
                "kind": a.kind,
                "recurrence": a.recurrence or None,
                "message": a.message,
                "task_id": a.task_id or None,
            },
        )
    )

    delete = sub.add_parser("delete")
    delete.add_argument("id")
    delete.set_defaults(handler=lambda a: _run("reminder.delete", {"id": a.id}))


def _run(tool: str, payload: dict) -> int:
    with app_session() as (session, _settings):
        outcome = PermissionGate(session, default_registry()).invoke(
            tool, payload, agent="reminder"
        )
    return print_outcome(outcome)
