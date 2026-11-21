"""Deterministic fallback when the LLM does not return a tool JSON object.

Used with FakeProvider and as a backup if a real model replies in prose.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Plan:
    tool: str | None
    payload: dict[str, Any]
    reply: str | None = None


_CREATE_TASK = re.compile(
    r"\b(?:create|add|new|make)\b.{0,20}\btasks?\b[:\s-]*(.+)$",
    re.I,
)
_UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
_COMPLETE_TASK = re.compile(
    r"\b(?:complete|finish|done|check off)\b.{0,40}\b(" + _UUID + r")\b",
    re.I,
)
_DELETE_TASK = re.compile(
    r"\b(?:delete|remove)\b.{0,20}\btasks?\b.{0,20}\b(" + _UUID + r")\b",
    re.I,
)
_PRIORITIZE = re.compile(
    r"\b(?:prioritize|priority)\b.{0,40}\b(low|medium|high)\b.{0,20}\b("
    + _UUID
    + r")\b",
    re.I,
)
_SUBTASK = re.compile(
    r"\bsubtask\b.{0,20}\b(" + _UUID + r")\b[:\s-]*(.+)$",
    re.I,
)
_REMIND = re.compile(
    r"\b(?:remind(?:er)?|remind me)\b[:\s-]*(.+)$",
    re.I,
)
_REMEMBER = re.compile(
    r"\bremember\b(?:\s+that)?\s+(\w+)\s+(?:is|=)\s+(.+)$",
    re.I,
)


def plan_from_text(text: str) -> Plan | None:
    stripped = text.strip()
    lower = stripped.lower()

    if lower in {"call me", "ping me", "alert me", "ring me"}:
        return Plan("alert.ping", {"text": "Jarvis checking in.", "call": "yes"})
    if lower in {
        "traffic",
        "how's traffic",
        "hows traffic",
        "commute",
        "office commute",
    }:
        return Plan("commute.traffic", {})
    if lower in {"news", "headlines", "daily news", "today's news", "todays news"}:
        return Plan("news.digest", {})
    if lower in {"morning briefing", "brief me", "daily briefing", "morning brief"}:
        return Plan("briefing.morning", {})
    if lower in {"evening briefing", "evening wrap", "wrap up"}:
        return Plan("briefing.evening", {})
    if lower in {"today's calendar", "todays calendar", "calendar today", "what's on today", "whats on today"}:
        return Plan("calendar.today", {})
    if lower in {"list calendar", "show calendar", "calendar"}:
        return Plan("calendar.list", {})
    if lower in {"list projects", "show projects", "projects"}:
        return Plan("project.list", {})
    if lower in {"github repos", "list repos", "my repos"}:
        return Plan("github.repos", {})
    if lower in {"notifications", "unread notifications", "list notifications"}:
        return Plan("notify.list", {})

    match = re.search(
        r"\b(?:commute city|set commute city|my city is|i live in)\b[:\s-]*(.+)$",
        stripped,
        re.I,
    )
    if match:
        return Plan("commute.set_city", {"city": match.group(1).strip().rstrip(".")})

    match = re.search(r"\b(?:create|add|new)\b.{0,20}\bproject\b[:\s-]*(.+)$", stripped, re.I)
    if match:
        return Plan("project.create", {"name": match.group(1).strip().rstrip(".")})
    match = re.search(
        r"\b(?:schedule|create event|add event|calendar)\b[:\s-]*(.+)$",
        stripped,
        re.I,
    )
    if match and "list" not in lower and "today" not in lower:
        rest = match.group(1).strip()
        when, title = _split_when(rest)
        payload: dict[str, Any] = {"title": title or rest}
        if when:
            payload["start_at"] = when
        return Plan("calendar.create", payload)
    match = re.search(r"\b(?:issues?|github issues)\b.{0,20}\b([\w.-]+/[\w.-]+)\b", stripped, re.I)
    if match:
        return Plan("github.issues", {"repo": match.group(1)})
    match = re.search(
        r"\b(?:pull requests?|prs|github pulls)\b.{0,20}\b([\w.-]+/[\w.-]+)\b",
        stripped,
        re.I,
    )
    if match:
        return Plan("github.pulls", {"repo": match.group(1)})
    match = re.search(r"\b(?:ingest|index)\b.{0,20}\b(?:doc|document|file)?[:\s-]*(.+)$", stripped, re.I)
    if match and ("doc" in lower or "ingest" in lower or "index" in lower):
        path = match.group(1).strip()
        if path:
            return Plan("docs.ingest", {"path": path})
    match = re.search(r"\b(?:search docs|search documents|find in docs)\b[:\s-]*(.+)$", stripped, re.I)
    if match:
        return Plan("docs.search", {"query": match.group(1).strip()})

    if lower in {"list emails", "show emails", "inbox", "list inbox"}:
        return Plan("email.list", {})
    if lower in {
        "check email",
        "check inbox",
        "fetch email",
        "fetch emails",
        "fetch inbox",
    }:
        return Plan("email.fetch", {"limit": 20})

    match = re.search(
        r"\b(?:summarize|summary)\b.{0,20}\bemail\b.{0,20}\b(" + _UUID + r")\b",
        stripped,
        re.I,
    )
    if match:
        return Plan("email.summarize", {"id": match.group(1)})
    match = re.search(
        r"\bdraft\b.{0,20}\b(?:reply|email)\b.{0,20}\b(" + _UUID + r")\b",
        stripped,
        re.I,
    )
    if match:
        return Plan("email.draft", {"id": match.group(1)})
    match = re.search(
        r"\bsend\b.{0,20}\b(?:email|reply)\b.{0,20}\b(" + _UUID + r")\b",
        stripped,
        re.I,
    )
    if match:
        return Plan("email.send", {"id": match.group(1)})
    match = re.search(r"\bsearch email(?:s)?\b[:\s-]*(.+)$", stripped, re.I)
    if match:
        return Plan("email.search", {"query": match.group(1).strip()})

    if lower in {"list tasks", "show tasks", "tasks", "what are my tasks"}:
        return Plan("task.list", {})
    if lower in {"list reminders", "show reminders", "reminders"}:
        return Plan("reminder.list", {})
    if lower in {"what's due", "whats due", "due reminders", "anything due"}:
        return Plan("reminder.due", {})

    match = _DELETE_TASK.search(stripped)
    if match:
        return Plan("task.delete", {"id": match.group(1)})

    match = _COMPLETE_TASK.search(stripped)
    if match:
        return Plan("task.complete", {"id": match.group(1)})

    match = _PRIORITIZE.search(stripped)
    if match:
        return Plan("task.prioritize", {"priority": match.group(1).lower(), "id": match.group(2)})

    match = _SUBTASK.search(stripped)
    if match:
        return Plan("task.add_subtask", {"parent_id": match.group(1), "title": match.group(2).strip()})

    match = _CREATE_TASK.search(stripped)
    if match:
        return Plan("task.create", {"title": match.group(1).strip().rstrip(".")})

    if "delete reminder" in lower:
        ident = _first_id(stripped)
        if ident:
            return Plan("reminder.delete", {"id": ident})

    match = _REMIND.search(stripped)
    if match:
        rest = match.group(1).strip()
        trigger, title = _split_when(rest)
        payload: dict[str, Any] = {"title": title, "trigger_at": trigger}
        if "every day" in lower or "daily" in lower:
            payload["kind"] = "recurring"
            payload["recurrence"] = "daily"
        elif "every week" in lower or "weekly" in lower:
            payload["kind"] = "recurring"
            payload["recurrence"] = "weekly"
        return Plan("reminder.create", payload)

    match = _REMEMBER.search(stripped)
    if match:
        return Plan(
            "memory.upsert",
            {
                "category": "USER_PROFILE",
                "key": match.group(1),
                "value": match.group(2).strip().rstrip("."),
            },
        )

    return None


def plan_from_llm_text(raw: str) -> Plan | None:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).removesuffix("```").strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end < 0:
            return None
        try:
            data = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None
    if not isinstance(data, dict):
        return None
    tool = data.get("tool")
    if tool is None:
        reply = data.get("reply")
        return Plan(None, {}, reply=str(reply) if reply else None)
    payload = data.get("payload") or {}
    if not isinstance(payload, dict):
        payload = {}
    return Plan(str(tool), payload)


def _first_id(text: str) -> str | None:
    match = re.search(_UUID, text, re.I)
    return match.group(0) if match else None


def _split_when(rest: str) -> tuple[str, str]:
    """Pull an ISO-ish datetime out if present; otherwise leave trigger empty."""
    match = re.search(r"\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2})?)?", rest)
    if match:
        trigger = match.group(0).replace(" ", "T")
        title = (rest[: match.start()] + rest[match.end() :]).strip(" ,at")
        return trigger, title or rest
    return "", rest
