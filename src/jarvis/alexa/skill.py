"""Turn an Alexa Skill JSON request into spoken Jarvis output."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from jarvis.agents.orchestrator import Orchestrator
from jarvis.commute.schedule import commute_card
from jarvis.commute.traffic import fetch_traffic, format_traffic
from jarvis.llm.factory import build_provider
from jarvis.news.feeds import fetch_digest, format_digest
from jarvis.security.gate import PermissionGate
from jarvis.tools.catalog import default_registry

_SPEAK_LIMIT = 700


def speakable(text: str, limit: int = _SPEAK_LIMIT) -> str:
    cleaned = " ".join(text.replace("\n", ". ").split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rsplit(" ", 1)[0] + "."


def alexa_response(text: str, *, end: bool = True) -> dict[str, Any]:
    speech = speakable(text)
    return {
        "version": "1.0",
        "response": {
            "outputSpeech": {"type": "PlainText", "text": speech},
            "shouldEndSession": end,
        },
    }


def handle_skill_body(body: dict[str, Any], session: Session) -> dict[str, Any]:
    request = body.get("request") or {}
    kind = str(request.get("type") or "")
    if kind == "LaunchRequest":
        card = commute_card(session=session)
        return alexa_response(
            f"{card} Ask me for traffic, briefing, or news.",
            end=False,
        )
    if kind == "SessionEndedRequest":
        return alexa_response("Goodbye.")
    if kind != "IntentRequest":
        return alexa_response("I did not catch that. Try traffic, briefing, or news.")

    intent = request.get("intent") or {}
    name = str(intent.get("name") or "")
    if name in {"AMAZON.StopIntent", "AMAZON.CancelIntent"}:
        return alexa_response("Okay.")
    if name == "AMAZON.HelpIntent":
        return alexa_response(
            "You can say traffic, morning briefing, news, or list tasks.",
            end=False,
        )
    if name == "TrafficIntent":
        return alexa_response(_tool(session, "commute.traffic"))
    if name == "BriefingIntent":
        return alexa_response(_short_briefing(session))
    if name == "NewsIntent":
        digest = format_digest(fetch_digest(include_topics=False, per_section=3))
        return alexa_response(digest)
    if name == "QueryIntent":
        slots = intent.get("slots") or {}
        query = ""
        if isinstance(slots, dict):
            raw = slots.get("query") or {}
            query = str(raw.get("value") or "").strip()
        if not query:
            return alexa_response("What do you want Jarvis to do?", end=False)
        orch = Orchestrator(session, build_provider())
        result = orch.handle(query)
        return alexa_response(result.reply)
    return alexa_response("Try saying traffic, briefing, or news.")


def _tool(session: Session, name: str) -> str:
    outcome = PermissionGate(session, default_registry()).invoke(
        name, {}, agent="alexa"
    )
    return outcome.message


def _short_briefing(session: Session) -> str:
    """Stay inside Alexa's ~8 second limit: skip full news topics."""
    parts = [commute_card(session=session)]
    traffic = fetch_traffic(session=session)
    parts.append(format_traffic(traffic))
    due = PermissionGate(session, default_registry()).invoke(
        "reminder.due", {}, agent="alexa"
    )
    if due.status == "ok" and due.message and "Nothing is due" not in due.message:
        parts.append(due.message)
    return " ".join(parts)
