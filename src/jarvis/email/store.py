from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from jarvis.core.clock import utc_now
from jarvis.db.models import Email
from jarvis.email.errors import EmailNotFoundError
from jarvis.email.transport import IncomingMessage
from jarvis.memory.errors import ValidationError


@dataclass(frozen=True)
class EmailRecord:
    id: str
    internet_id: str
    from_addr: str
    to_addr: str
    subject: str
    body: str
    received_at: datetime
    category: str | None
    urgency: str | None
    deadline_note: str | None
    summary: str | None
    draft_reply: str | None
    sent_at: datetime | None


def _to_record(row: Email) -> EmailRecord:
    return EmailRecord(
        id=row.id,
        internet_id=row.internet_id,
        from_addr=row.from_addr,
        to_addr=row.to_addr,
        subject=row.subject,
        body=row.body,
        received_at=row.received_at,
        category=row.category,
        urgency=row.urgency,
        deadline_note=row.deadline_note,
        summary=row.summary,
        draft_reply=row.draft_reply,
        sent_at=row.sent_at,
    )


class EmailStore:
    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert_incoming(self, incoming: IncomingMessage) -> EmailRecord:
        existing = self._session.scalar(
            select(Email).where(Email.internet_id == incoming.internet_id)
        )
        now = utc_now()
        if existing is None:
            row = Email(
                id=str(uuid4()),
                internet_id=incoming.internet_id,
                from_addr=incoming.from_addr,
                to_addr=incoming.to_addr,
                subject=incoming.subject,
                body=incoming.body,
                received_at=incoming.received_at,
                category=None,
                urgency=None,
                deadline_note=None,
                summary=None,
                draft_reply=None,
                sent_at=None,
                created_at=now,
                updated_at=now,
            )
            self._session.add(row)
        else:
            row = existing
            row.from_addr = incoming.from_addr
            row.to_addr = incoming.to_addr
            row.subject = incoming.subject
            row.body = incoming.body
            row.received_at = incoming.received_at
            row.updated_at = now
        self._session.flush()
        return _to_record(row)

    def get(self, email_id: str) -> EmailRecord:
        return _to_record(self._require(email_id))

    def list(self, *, category: str | None = None, limit: int = 20) -> list[EmailRecord]:
        stmt = select(Email).order_by(Email.received_at.desc()).limit(max(1, min(limit, 100)))
        if category:
            stmt = stmt.where(Email.category == category)
        return [_to_record(row) for row in self._session.scalars(stmt).all()]

    def search(self, query: str) -> list[EmailRecord]:
        q = query.strip()
        if not q:
            raise ValidationError("Search query cannot be empty.")
        pattern = f"%{q}%"
        stmt = (
            select(Email)
            .where(
                or_(
                    Email.subject.ilike(pattern),
                    Email.body.ilike(pattern),
                    Email.from_addr.ilike(pattern),
                )
            )
            .order_by(Email.received_at.desc())
            .limit(50)
        )
        return [_to_record(row) for row in self._session.scalars(stmt).all()]

    def update_classification(
        self,
        email_id: str,
        *,
        category: str,
        urgency: str,
        deadline_note: str | None,
        summary: str | None = None,
    ) -> EmailRecord:
        row = self._require(email_id)
        row.category = category
        row.urgency = urgency
        row.deadline_note = deadline_note
        if summary is not None:
            row.summary = summary
        row.updated_at = utc_now()
        self._session.flush()
        return _to_record(row)

    def set_summary(self, email_id: str, summary: str) -> EmailRecord:
        row = self._require(email_id)
        row.summary = summary
        row.updated_at = utc_now()
        self._session.flush()
        return _to_record(row)

    def set_draft(self, email_id: str, draft: str) -> EmailRecord:
        if not draft.strip():
            raise ValidationError("Draft reply cannot be empty.")
        row = self._require(email_id)
        row.draft_reply = draft.strip()
        row.updated_at = utc_now()
        self._session.flush()
        return _to_record(row)

    def mark_sent(self, email_id: str) -> EmailRecord:
        row = self._require(email_id)
        row.sent_at = utc_now()
        row.updated_at = utc_now()
        self._session.flush()
        return _to_record(row)

    def _require(self, email_id: str) -> Email:
        row = self._session.get(Email, email_id)
        if row is None:
            raise EmailNotFoundError(
                f"No cached email {email_id!r}. Run `jarvis email fetch` then `jarvis email list`."
            )
        return row
