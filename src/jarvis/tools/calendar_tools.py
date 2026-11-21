from __future__ import annotations

from datetime import timedelta
from typing import Any

from sqlalchemy.orm import Session

from jarvis.calendar.store import CalendarStore
from jarvis.core.clock import utc_now
from jarvis.core.dates import parse_datetime
from jarvis.notify.store import NotificationStore
from jarvis.security.levels import PermissionLevel
from jarvis.tools.base import Tool, ToolResult
from jarvis.tools.serialize import record_data


def _store(session: Session) -> CalendarStore:
    return CalendarStore(session)


class CalendarTodayTool(Tool):
    name = "calendar.today"
    description = "List events for today."
    agent = "calendar"
    level = PermissionLevel.READ

    def run(self, session: Session, payload: dict[str, Any]) -> ToolResult:
        del payload
        records = _store(session).today()
        if not records:
            return ToolResult(True, "No events today.", {"items": []})
        lines = [f"{r.start_at.isoformat()} {r.id[:8]} {r.title}" for r in records]
        return ToolResult(True, "\n".join(lines), {"items": [record_data(r) for r in records]})


class CalendarListTool(Tool):
    name = "calendar.list"
    description = "List events between start and end datetimes."
    agent = "calendar"
    level = PermissionLevel.READ

    def run(self, session: Session, payload: dict[str, Any]) -> ToolResult:
        start_raw = payload.get("start") or utc_now().strftime("%Y-%m-%d")
        end_raw = payload.get("end")
        start = parse_datetime(str(start_raw))
        end = parse_datetime(str(end_raw)) if end_raw else start + timedelta(days=7)
        records = _store(session).list_range(start, end)
        if not records:
            return ToolResult(True, "No events in that range.", {"items": []})
        lines = [f"{r.start_at.isoformat()} {r.id[:8]} {r.title}" for r in records]
        return ToolResult(True, "\n".join(lines), {"items": [record_data(r) for r in records]})


class CalendarCreateTool(Tool):
    name = "calendar.create"
    description = "Create a calendar event. Warns on overlaps."
    agent = "calendar"
    level = PermissionLevel.SAFE

    def run(self, session: Session, payload: dict[str, Any]) -> ToolResult:
        record, conflicts = _store(session).create(
            str(payload.get("title", "")),
            str(payload.get("start_at") or payload.get("start") or ""),
            end_at=payload.get("end_at") or payload.get("end") or None,
            location=str(payload.get("location", "")),
            notes=str(payload.get("notes", "")),
        )
        message = f"Created event {record.id[:8]}: {record.title} at {record.start_at.isoformat()}"
        if conflicts:
            names = ", ".join(c.title for c in conflicts)
            message += f" (overlaps: {names})"
            NotificationStore(session).add(
                "calendar",
                "Schedule overlap",
                f"{record.title} overlaps {names}",
            )
        return ToolResult(
            True,
            message,
            {"event": record_data(record), "conflicts": [record_data(c) for c in conflicts]},
        )


class CalendarDeleteTool(Tool):
    name = "calendar.delete"
    description = "Delete a calendar event. Requires confirmation."
    agent = "calendar"
    level = PermissionLevel.CONFIRM

    def run(self, session: Session, payload: dict[str, Any]) -> ToolResult:
        record = _store(session).delete(str(payload.get("id", "")))
        return ToolResult(True, f"Deleted event {record.title}.", record_data(record))
