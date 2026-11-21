from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from jarvis.projects.store import ProjectStore
from jarvis.security.levels import PermissionLevel
from jarvis.tools.base import Tool, ToolResult
from jarvis.tools.serialize import record_data


def _store(session: Session) -> ProjectStore:
    return ProjectStore(session)


class ProjectListTool(Tool):
    name = "project.list"
    description = "List projects."
    agent = "project"
    level = PermissionLevel.READ

    def run(self, session: Session, payload: dict[str, Any]) -> ToolResult:
        records = _store(session).list(status=payload.get("status") or None)
        if not records:
            return ToolResult(True, "No projects.", {"items": []})
        lines = [f"{r.status} {r.id[:8]} {r.name}" for r in records]
        return ToolResult(True, "\n".join(lines), {"items": [record_data(r) for r in records]})


class ProjectCreateTool(Tool):
    name = "project.create"
    description = "Create a named project."
    agent = "project"
    level = PermissionLevel.SAFE

    def run(self, session: Session, payload: dict[str, Any]) -> ToolResult:
        record = _store(session).create(
            str(payload.get("name", "")),
            description=str(payload.get("description", "")),
            status=str(payload.get("status", "active")),
        )
        return ToolResult(
            True,
            f"Created project {record.id[:8]}: {record.name}",
            record_data(record),
        )


class ProjectUpdateTool(Tool):
    name = "project.update"
    description = "Update a project's status or description."
    agent = "project"
    level = PermissionLevel.SAFE

    def run(self, session: Session, payload: dict[str, Any]) -> ToolResult:
        record = _store(session).update(
            str(payload.get("id", "")),
            status=payload.get("status"),
            description=payload.get("description"),
        )
        return ToolResult(True, f"Updated project {record.name}.", record_data(record))
