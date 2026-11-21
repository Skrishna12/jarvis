from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from jarvis.alerts.watch import Alert, deliver_alerts
from jarvis.config import load_settings
from jarvis.security.levels import PermissionLevel
from jarvis.tools.base import Tool, ToolResult


class AlertPingTool(Tool):
    name = "alert.ping"
    description = "Send an update now (Telegram + optional phone call)."
    agent = "alert"
    level = PermissionLevel.SAFE

    def run(self, session: Session, payload: dict[str, Any]) -> ToolResult:
        text = str(payload.get("text") or payload.get("message") or "").strip()
        if not text:
            text = "Jarvis checking in. No extra details."
        call = str(payload.get("call") or "yes").lower() not in {"no", "false", "0"}
        settings = load_settings()
        notes = deliver_alerts(
            session,
            [Alert("manual", "Jarvis update", text, call=call and settings.alert_call)],
            settings=settings,
        )
        extra = " I would also place a call." if call and settings.alert_call else ""
        if settings.voice_backend == "fake" and call:
            extra = " Call is in fake mode (spoken locally, phone not dialed)."
        return ToolResult(True, "Update queued." + extra, {"notes": notes})
