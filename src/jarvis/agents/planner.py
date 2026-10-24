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
