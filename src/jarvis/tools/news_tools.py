from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from jarvis.news.feeds import fetch_digest, format_digest
from jarvis.security.levels import PermissionLevel
from jarvis.tools.base import Tool, ToolResult


class NewsDigestTool(Tool):
    name = "news.digest"
    description = "National, international, and topic headlines from public RSS."
    agent = "news"
    level = PermissionLevel.READ

    def run(self, session: Session, payload: dict[str, Any]) -> ToolResult:
        del session
        include_topics = str(payload.get("topics", "yes")).lower() not in {"no", "false", "0"}
        sections = fetch_digest(include_topics=include_topics)
        data = {
            "sections": [
                {
                    "name": s.name,
                    "error": s.error,
                    "headlines": [{"title": h.title, "link": h.link} for h in s.headlines],
                }
                for s in sections
            ]
        }
        return ToolResult(True, format_digest(sections), data)
