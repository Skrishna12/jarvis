from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from jarvis.config import load_settings
from jarvis.email.classify import draft_reply_text, hint, summarize_text
from jarvis.email.store import EmailStore
from jarvis.email.transport import build_transport
from jarvis.llm.factory import build_provider
from jarvis.memory.errors import ValidationError
from jarvis.security.levels import PermissionLevel
from jarvis.tools.base import Tool, ToolResult
from jarvis.tools.serialize import record_data


def _store(session: Session) -> EmailStore:
    return EmailStore(session)


class EmailFetchTool(Tool):
    name = "email.fetch"
    description = "Pull recent inbox messages into the local cache."
    agent = "email"
    level = PermissionLevel.READ

    def run(self, session: Session, payload: dict[str, Any]) -> ToolResult:
        limit = int(payload.get("limit") or 20)
        transport = build_transport()
        incoming = transport.fetch_recent(limit)
        store = _store(session)
        records = []
        for message in incoming:
            record = store.upsert_incoming(message)
            hints = hint(record.subject, record.body)
            record = store.update_classification(
                record.id,
                category=hints.category.value,
                urgency=hints.urgency.value,
                deadline_note=hints.deadline_note,
            )
            records.append(record)
        if not records:
            return ToolResult(True, "Inbox fetch returned no messages.", {"items": []})
        lines = [
            f"{r.urgency or '-'} {r.category or '-'} {r.id[:8]} {r.subject}"
            for r in records
        ]
        return ToolResult(
            True,
            "Fetched:\n" + "\n".join(lines),
            {"items": [record_data(r) for r in records]},
        )


class EmailListTool(Tool):
    name = "email.list"
    description = "List cached emails, optionally by category."
    agent = "email"
    level = PermissionLevel.READ

    def run(self, session: Session, payload: dict[str, Any]) -> ToolResult:
        records = _store(session).list(
            category=payload.get("category") or None,
            limit=int(payload.get("limit") or 20),
        )
        if not records:
            return ToolResult(
                True,
                "No cached emails. Run email.fetch first.",
                {"items": []},
            )
        lines = [
            f"{r.urgency or '-'} {r.category or '-'} {r.id[:8]} {r.subject}"
            for r in records
        ]
        return ToolResult(True, "\n".join(lines), {"items": [record_data(r) for r in records]})


class EmailGetTool(Tool):
    name = "email.get"
    description = "Show one cached email."
    agent = "email"
    level = PermissionLevel.READ

    def run(self, session: Session, payload: dict[str, Any]) -> ToolResult:
        record = _store(session).get(str(payload.get("id", "")))
        preview = record.body[:400]
        extra = f"\nDeadline: {record.deadline_note}" if record.deadline_note else ""
        return ToolResult(
            True,
            f"From {record.from_addr}\n{record.subject}\n{preview}{extra}",
            record_data(record),
        )


class EmailSearchTool(Tool):
    name = "email.search"
    description = "Search cached emails by subject, body, or sender."
    agent = "email"
    level = PermissionLevel.READ

    def run(self, session: Session, payload: dict[str, Any]) -> ToolResult:
        records = _store(session).search(str(payload.get("query", "")))
        if not records:
            return ToolResult(True, "No matches.", {"items": []})
        lines = [f"{r.id[:8]} {r.subject}" for r in records]
        return ToolResult(True, "\n".join(lines), {"items": [record_data(r) for r in records]})


class EmailClassifyTool(Tool):
    name = "email.classify"
    description = "Classify one cached email (topic, urgency, deadline hint)."
    agent = "email"
    level = PermissionLevel.READ

    def run(self, session: Session, payload: dict[str, Any]) -> ToolResult:
        store = _store(session)
        record = store.get(str(payload.get("id", "")))
        hints = hint(record.subject, record.body)
        updated = store.update_classification(
            record.id,
            category=hints.category.value,
            urgency=hints.urgency.value,
            deadline_note=hints.deadline_note,
        )
        note = f" Deadline: {updated.deadline_note}." if updated.deadline_note else ""
        return ToolResult(
            True,
            f"{updated.subject} → {updated.category} ({updated.urgency}).{note}",
            record_data(updated),
        )


class EmailSummarizeTool(Tool):
    name = "email.summarize"
    description = "Summarize one cached email."
    agent = "email"
    level = PermissionLevel.READ

    def run(self, session: Session, payload: dict[str, Any]) -> ToolResult:
        store = _store(session)
        record = store.get(str(payload.get("id", "")))
        provider = build_provider(load_settings())
        summary = summarize_text(provider, record.subject, record.body)
        updated = store.set_summary(record.id, summary)
        return ToolResult(True, summary, record_data(updated))


class EmailDraftTool(Tool):
    name = "email.draft"
    description = "Draft a reply. Does not send."
    agent = "email"
    level = PermissionLevel.SAFE

    def run(self, session: Session, payload: dict[str, Any]) -> ToolResult:
        store = _store(session)
        record = store.get(str(payload.get("id", "")))
        body = str(payload.get("body") or "").strip()
        if not body:
            provider = build_provider(load_settings())
            body = draft_reply_text(provider, record.subject, record.body)
        updated = store.set_draft(record.id, body)
        return ToolResult(
            True,
            "Draft saved (not sent):\n" + body,
            record_data(updated),
        )


class EmailSendTool(Tool):
    name = "email.send"
    description = "Send the saved draft. Requires confirmation."
    agent = "email"
    level = PermissionLevel.CONFIRM

    def run(self, session: Session, payload: dict[str, Any]) -> ToolResult:
        store = _store(session)
        record = store.get(str(payload.get("id", "")))
        if not record.draft_reply:
            raise ValidationError(
                "No draft to send. Run email.draft first, then confirm send."
            )
        if record.sent_at is not None:
            raise ValidationError("This draft was already sent.")
        to = record.from_addr
        subject = record.subject if record.subject.lower().startswith("re:") else f"Re: {record.subject}"
        build_transport().send(to=to, subject=subject, body=record.draft_reply)
        updated = store.mark_sent(record.id)
        return ToolResult(
            True,
            f"Sent reply to {to} subject {subject!r}.",
            record_data(updated),
        )
