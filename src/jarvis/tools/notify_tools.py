from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from jarvis.notify.store import NotificationStore
from jarvis.security.levels import PermissionLevel
from jarvis.tools.base import Tool, ToolResult
from jarvis.tools.serialize import record_data


class NotifyListTool(Tool):
    name = "notify.list"
    description = "List unread in-app notifications."
    agent = "notify"
    level = PermissionLevel.READ

    def run(self, session: Session, payload: dict[str, Any]) -> ToolResult:
        records = NotificationStore(session).unread(int(payload.get("limit") or 20))
        if not records:
            return ToolResult(True, "No unread notifications.", {"items": []})
        lines = [f"{r.source} {r.id[:8]} {r.title}" for r in records]
        return ToolResult(True, "\n".join(lines), {"items": [record_data(r) for r in records]})


class NotifyReadTool(Tool):
    name = "notify.read"
    description = "Mark one notification as read."
    agent = "notify"
    level = PermissionLevel.SAFE

    def run(self, session: Session, payload: dict[str, Any]) -> ToolResult:
        record = NotificationStore(session).mark_read(str(payload.get("id", "")))
        if record is None:
            return ToolResult(False, "No notification with that id.")
        return ToolResult(True, f"Marked read: {record.title}", record_data(record))
