from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from jarvis.reminders.store import ReminderStore
from jarvis.security.levels import PermissionLevel
from jarvis.tools.base import Tool, ToolResult
from jarvis.tools.serialize import record_data


def _store(session: Session) -> ReminderStore:
    return ReminderStore(session)


class ReminderListTool(Tool):
    name = "reminder.list"
    description = "List reminders."
    agent = "reminder"
    level = PermissionLevel.READ

    def run(self, session: Session, payload: dict[str, Any]) -> ToolResult:
        del payload
        records = _store(session).list()
        if not records:
            return ToolResult(True, "No reminders.", {"items": []})
        lines = [
            f"{r.kind} {r.trigger_at.isoformat()} {r.id[:8]} {r.title}"
            for r in records
        ]
        return ToolResult(True, "\n".join(lines), {"items": [record_data(r) for r in records]})


class ReminderDueTool(Tool):
    name = "reminder.due"
    description = "List reminders whose time has arrived."
    agent = "reminder"
    level = PermissionLevel.READ

    def run(self, session: Session, payload: dict[str, Any]) -> ToolResult:
        del payload
        store = _store(session)
        records = store.due()
        if not records:
            return ToolResult(True, "Nothing is due.", {"items": []})
        fired = [store.mark_fired(r.id) for r in records]
        lines = [f"{r.title}: {r.message}" for r in records]
        return ToolResult(
            True,
            "Due now:\n" + "\n".join(lines),
            {"items": [record_data(r) for r in records], "updated": [record_data(r) for r in fired]},
        )


class ReminderCreateTool(Tool):
    name = "reminder.create"
    description = "Create a one-time, recurring, or deadline reminder."
    agent = "reminder"
    level = PermissionLevel.SAFE

    def run(self, session: Session, payload: dict[str, Any]) -> ToolResult:
        record = _store(session).create(
            str(payload.get("title", "")),
            message=str(payload.get("message", "")),
            kind=str(payload.get("kind", "one_time")),
            trigger_at=str(payload.get("trigger_at", "")),
            recurrence=payload.get("recurrence"),
            task_id=payload.get("task_id") or None,
        )
        return ToolResult(
            True,
            f"Reminder {record.id[:8]} at {record.trigger_at.isoformat()}: {record.title}",
            record_data(record),
        )


class ReminderDeleteTool(Tool):
    name = "reminder.delete"
    description = "Delete a reminder. Requires confirmation."
    agent = "reminder"
    level = PermissionLevel.CONFIRM

    def run(self, session: Session, payload: dict[str, Any]) -> ToolResult:
        record = _store(session).delete(str(payload.get("id", "")))
        return ToolResult(True, f"Deleted reminder {record.title}.", record_data(record))
