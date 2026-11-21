from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from jarvis.commute.schedule import commute_card, resolve_city
from jarvis.commute.traffic import fetch_traffic, format_traffic
from jarvis.memory.store import MemoryStore
from jarvis.security.levels import PermissionLevel
from jarvis.tools.base import Tool, ToolResult


class CommuteStatusTool(Tool):
    name = "commute.status"
    description = "Weekday office hours and commute city."
    agent = "commute"
    level = PermissionLevel.READ

    def run(self, session: Session, payload: dict[str, Any]) -> ToolResult:
        del payload
        text = commute_card(session=session)
        return ToolResult(True, text, {"city": resolve_city(session)})


class CommuteTrafficTool(Tool):
    name = "commute.traffic"
    description = "Traffic and delay headlines for the commute city."
    agent = "commute"
    level = PermissionLevel.READ

    def run(self, session: Session, payload: dict[str, Any]) -> ToolResult:
        del payload
        section = fetch_traffic(session=session)
        return ToolResult(
            True,
            commute_card(session=session) + "\n" + format_traffic(section),
            {
                "city": resolve_city(session),
                "error": section.error,
                "headlines": [h.title for h in section.headlines],
            },
        )


class CommuteSetCityTool(Tool):
    name = "commute.set_city"
    description = "Remember the city used for traffic headlines."
    agent = "commute"
    level = PermissionLevel.SAFE

    def run(self, session: Session, payload: dict[str, Any]) -> ToolResult:
        city = str(payload.get("city") or "").strip()
        if not city:
            return ToolResult(
                False,
                "Tell me the city, e.g. commute.set_city city=Hyderabad.",
            )
        MemoryStore(session).upsert("USER_PROFILE", "commute_city", city)
        return ToolResult(True, f"I'll use {city} for traffic headlines.", {"city": city})
