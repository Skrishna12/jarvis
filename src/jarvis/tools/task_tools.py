from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from jarvis.security.levels import PermissionLevel
from jarvis.tasks.store import TaskStore
from jarvis.tools.base import Tool, ToolResult
from jarvis.tools.serialize import record_data


def _store(session: Session) -> TaskStore:
    return TaskStore(session)


class TaskListTool(Tool):
    name = "task.list"
    description = "List tasks, optionally filtered by status."
    agent = "task"
    level = PermissionLevel.READ

    def run(self, session: Session, payload: dict[str, Any]) -> ToolResult:
        records = _store(session).list(
            status=payload.get("status") or None,
            parent_id=payload.get("parent_id") or None,
        )
        if not records:
            return ToolResult(True, "No tasks.", {"items": []})
        lines = [f"{r.priority} {r.status} {r.id[:8]} {r.title}" for r in records]
        return ToolResult(True, "\n".join(lines), {"items": [record_data(r) for r in records]})


class TaskGetTool(Tool):
    name = "task.get"
    description = "Show one task by id."
    agent = "task"
    level = PermissionLevel.READ

    def run(self, session: Session, payload: dict[str, Any]) -> ToolResult:
        record = _store(session).get(str(payload.get("id", "")))
        return ToolResult(True, f"{record.status} {record.title}", record_data(record))


class TaskCreateTool(Tool):
    name = "task.create"
    description = "Create a task."
    agent = "task"
    level = PermissionLevel.SAFE

    def run(self, session: Session, payload: dict[str, Any]) -> ToolResult:
        record = _store(session).create(
            str(payload.get("title", "")),
            description=str(payload.get("description", "")),
            priority=str(payload.get("priority", "medium")),
            parent_id=payload.get("parent_id") or None,
            due_at=payload.get("due_at") or None,
        )
        return ToolResult(True, f"Created task {record.id[:8]}: {record.title}", record_data(record))


class TaskUpdateTool(Tool):
    name = "task.update"
    description = "Update task fields."
    agent = "task"
    level = PermissionLevel.SAFE

    def run(self, session: Session, payload: dict[str, Any]) -> ToolResult:
        record = _store(session).update(
            str(payload.get("id", "")),
            title=payload.get("title"),
            description=payload.get("description"),
            status=payload.get("status"),
            priority=payload.get("priority"),
            due_at=payload.get("due_at"),
        )
        return ToolResult(True, f"Updated task {record.id[:8]}.", record_data(record))


class TaskCompleteTool(Tool):
    name = "task.complete"
    description = "Mark a task done."
    agent = "task"
    level = PermissionLevel.SAFE

    def run(self, session: Session, payload: dict[str, Any]) -> ToolResult:
        record = _store(session).complete(str(payload.get("id", "")))
        return ToolResult(True, f"Completed {record.title}.", record_data(record))


class TaskPrioritizeTool(Tool):
    name = "task.prioritize"
    description = "Set task priority to low, medium, or high."
    agent = "task"
    level = PermissionLevel.SAFE

    def run(self, session: Session, payload: dict[str, Any]) -> ToolResult:
        record = _store(session).prioritize(
            str(payload.get("id", "")),
            str(payload.get("priority", "")),
        )
        return ToolResult(
            True,
            f"Priority for {record.title} is now {record.priority}.",
            record_data(record),
        )


class TaskAddSubtaskTool(Tool):
    name = "task.add_subtask"
    description = "Add a subtask under a parent task."
    agent = "task"
    level = PermissionLevel.SAFE

    def run(self, session: Session, payload: dict[str, Any]) -> ToolResult:
        record = _store(session).add_subtask(
            str(payload.get("parent_id", "")),
            str(payload.get("title", "")),
            description=str(payload.get("description", "")),
            priority=str(payload.get("priority", "medium")),
            due_at=payload.get("due_at") or None,
        )
        return ToolResult(
            True,
            f"Added subtask {record.id[:8]}: {record.title}",
            record_data(record),
        )


class TaskDeleteTool(Tool):
    name = "task.delete"
    description = "Delete a task. Requires confirmation."
    agent = "task"
    level = PermissionLevel.CONFIRM

    def run(self, session: Session, payload: dict[str, Any]) -> ToolResult:
        record = _store(session).delete(str(payload.get("id", "")))
        return ToolResult(True, f"Deleted task {record.title}.", record_data(record))
