from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from jarvis.calendar.store import CalendarStore
from jarvis.commute.schedule import commute_card
from jarvis.commute.traffic import fetch_traffic, format_traffic
from jarvis.email.store import EmailStore
from jarvis.news.feeds import fetch_digest, format_digest
from jarvis.notify.store import NotificationStore
from jarvis.reminders.store import ReminderStore
from jarvis.security.levels import PermissionLevel
from jarvis.tasks.store import TaskStore
from jarvis.tools.base import Tool, ToolResult
from jarvis.tools.serialize import record_data


class BriefingMorningTool(Tool):
    name = "briefing.morning"
    description = (
        "Today's events, due reminders, open high tasks, unread mail, and daily news."
    )
    agent = "briefing"
    level = PermissionLevel.SAFE

    def run(self, session: Session, payload: dict[str, Any]) -> ToolResult:
        del payload
        due = ReminderStore(session).due()
        events = CalendarStore(session).today()
        tasks = [t for t in TaskStore(session).list(status="open") if t.priority == "high"]
        notices = NotificationStore(session).unread()
        mail = EmailStore(session).list(limit=5)
        sections: list[str] = ["Morning briefing", commute_card(session=session)]
        traffic = fetch_traffic(session=session)
        sections.append(format_traffic(traffic))
        if due:
            sections.append("Due: " + ", ".join(r.title for r in due))
        else:
            sections.append("Due: nothing")
        if events:
            sections.append(
                "Today: "
                + ", ".join(f"{e.start_at.strftime('%H:%M')} {e.title}" for e in events)
            )
        else:
            sections.append("Today: no events")
        if tasks:
            sections.append("High tasks: " + ", ".join(t.title for t in tasks))
        if notices:
            sections.append(f"Notifications: {len(notices)} unread")
        if mail:
            sections.append("Recent mail: " + ", ".join(m.subject for m in mail[:3]))
        news = fetch_digest()
        sections.append(format_digest(news))
        return ToolResult(
            True,
            "\n".join(sections),
            {
                "due": [record_data(r) for r in due],
                "events": [record_data(e) for e in events],
                "tasks": [record_data(t) for t in tasks],
                "notifications": [record_data(n) for n in notices],
                "news": [
                    {
                        "name": s.name,
                        "error": s.error,
                        "headlines": [h.title for h in s.headlines],
                    }
                    for s in news
                ],
            },
        )


class BriefingEveningTool(Tool):
    name = "briefing.evening"
    description = "Open tasks and leftover unread notifications."
    agent = "briefing"
    level = PermissionLevel.READ

    def run(self, session: Session, payload: dict[str, Any]) -> ToolResult:
        del payload
        open_tasks = TaskStore(session).list(status="open")
        notices = NotificationStore(session).unread()
        lines = ["Evening wrap-up", commute_card(session=session)]
        traffic = fetch_traffic(session=session)
        lines.append(format_traffic(traffic))
        if open_tasks:
            lines.append("Still open: " + ", ".join(t.title for t in open_tasks[:10]))
        else:
            lines.append("No open tasks.")
        lines.append(f"Unread notifications: {len(notices)}")
        return ToolResult(
            True,
            "\n".join(lines),
            {
                "tasks": [record_data(t) for t in open_tasks],
                "notifications": [record_data(n) for n in notices],
            },
        )
