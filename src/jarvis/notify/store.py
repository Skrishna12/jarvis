from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from jarvis.core.clock import utc_now
from jarvis.db.models import Notification


@dataclass(frozen=True)
class NotificationRecord:
    id: str
    source: str
    title: str
    body: str
    read: bool
    created_at: datetime


def _to_record(row: Notification) -> NotificationRecord:
    return NotificationRecord(
        id=row.id,
        source=row.source,
        title=row.title,
        body=row.body,
        read=row.read,
        created_at=row.created_at,
    )


class NotificationStore:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, source: str, title: str, body: str) -> NotificationRecord:
        row = Notification(
            id=str(uuid4()),
            source=source.strip() or "jarvis",
            title=title.strip() or "Notice",
            body=body.strip(),
            read=False,
            created_at=utc_now(),
        )
        self._session.add(row)
        self._session.flush()
        return _to_record(row)

    def unread(self, limit: int = 20) -> list[NotificationRecord]:
        stmt = (
            select(Notification)
            .where(Notification.read.is_(False))
            .order_by(Notification.created_at.desc())
            .limit(max(1, min(limit, 100)))
        )
        return [_to_record(row) for row in self._session.scalars(stmt).all()]

    def mark_read(self, notification_id: str) -> NotificationRecord | None:
        row = self._session.get(Notification, notification_id)
        if row is None:
            return None
        row.read = True
        self._session.flush()
        return _to_record(row)
