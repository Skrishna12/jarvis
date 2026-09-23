"""Append-only store for conversation turns.

Summarizing these rows into memories.CONVERSATION_CONTEXT is not implemented
here. That policy is decided at Milestone 7 with an explicit choice.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from jarvis.db.models import ConversationMessage
from jarvis.memory.errors import ValidationError

_MAX_CONTENT_LEN = 32_768


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass(frozen=True)
class ConversationRecord:
    id: str
    role: MessageRole
    content: str
    created_at: datetime


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _parse_role(raw: str) -> MessageRole:
    try:
        return MessageRole(raw)
    except ValueError as exc:
        allowed = ", ".join(r.value for r in MessageRole)
        raise ValidationError(
            f"Unknown message role {raw!r}. Use one of: {allowed}."
        ) from exc


class ConversationStore:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, role: str, content: str) -> ConversationRecord:
        parsed_role = _parse_role(role)
        text = content.strip()
        if not text:
            raise ValidationError("Message content cannot be empty.")
        if len(text) > _MAX_CONTENT_LEN:
            raise ValidationError(
                f"Message content is {len(text)} characters; "
                f"max is {_MAX_CONTENT_LEN}."
            )
        row = ConversationMessage(
            id=str(uuid4()),
            role=parsed_role.value,
            content=text,
            created_at=_utc_now(),
        )
        self._session.add(row)
        self._session.flush()
        return ConversationRecord(
            id=row.id,
            role=parsed_role,
            content=row.content,
            created_at=row.created_at,
        )

    def recent(self, limit: int = 20) -> list[ConversationRecord]:
        if limit < 1:
            raise ValidationError("limit must be at least 1.")
        if limit > 500:
            raise ValidationError("limit cannot exceed 500.")
        rows = self._session.scalars(
            select(ConversationMessage)
            .order_by(ConversationMessage.created_at.desc())
            .limit(limit)
        ).all()
        # Oldest of the window first — easier to read as a transcript.
        ordered = list(reversed(rows))
        return [
            ConversationRecord(
                id=row.id,
                role=MessageRole(row.role),
                content=row.content,
                created_at=row.created_at,
            )
            for row in ordered
        ]
