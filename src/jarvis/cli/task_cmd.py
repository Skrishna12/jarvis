from __future__ import annotations

import argparse

from jarvis.cli.outcome import print_outcome
from jarvis.runtime import app_session
from jarvis.security.gate import PermissionGate
from jarvis.tools.catalog import default_registry


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("task", help="Task tools (go through the permission gate).")
    sub = parser.add_subparsers(dest="task_command", required=True)

    listed = sub.add_parser("list")
    listed.add_argument("--status", default="")
    listed.set_defaults(handler=lambda a: _run("task.list", {"status": a.status or None}))

    get_p = sub.add_parser("get")
    get_p.add_argument("id")
    get_p.set_defaults(handler=lambda a: _run("task.get", {"id": a.id}))

    create = sub.add_parser("create")
    create.add_argument("title")
    create.add_argument("--priority", default="medium")
    create.add_argument("--due-at", dest="due_at", default="")
    create.add_argument("--description", default="")
    create.set_defaults(
        handler=lambda a: _run(
            "task.create",
            {
                "title": a.title,
                "priority": a.priority,
                "due_at": a.due_at or None,
                "description": a.description,
            },
        )
    )

    complete = sub.add_parser("complete")
    complete.add_argument("id")
    complete.set_defaults(handler=lambda a: _run("task.complete", {"id": a.id}))

    prio = sub.add_parser("prioritize")
    prio.add_argument("id")
    prio.add_argument("priority")
    prio.set_defaults(
        handler=lambda a: _run("task.prioritize", {"id": a.id, "priority": a.priority})
    )

    subtask = sub.add_parser("subtask")
    subtask.add_argument("parent_id")
    subtask.add_argument("title")
    subtask.set_defaults(
        handler=lambda a: _run("task.add_subtask", {"parent_id": a.parent_id, "title": a.title})
    )

    delete = sub.add_parser("delete")
    delete.add_argument("id")
    delete.set_defaults(handler=lambda a: _run("task.delete", {"id": a.id}))


def _run(tool: str, payload: dict) -> int:
    with app_session() as (session, _settings):
        outcome = PermissionGate(session, default_registry()).invoke(tool, payload, agent="task")
    return print_outcome(outcome)
