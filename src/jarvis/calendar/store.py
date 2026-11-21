from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from jarvis.core.clock import utc_now
from jarvis.core.dates import DateParseError, parse_datetime
from jarvis.db.models import CalendarEvent
from jarvis.memory.errors import ValidationError


class EventNotFoundError(LookupError):
    pass


@dataclass(frozen=True)
class CalendarRecord:
    id: str
    title: str
    start_at: datetime
    end_at: datetime
    location: str
    notes: str
    created_at: datetime
    updated_at: datetime


def _to_record(row: CalendarEvent) -> CalendarRecord:
    return CalendarRecord(
        id=row.id,
        title=row.title,
        start_at=row.start_at,
        end_at=row.end_at,
        location=row.location,
        notes=row.notes,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class CalendarStore:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        title: str,
        start_at: str,
        *,
        end_at: str | None = None,
        location: str = "",
        notes: str = "",
    ) -> tuple[CalendarRecord, list[CalendarRecord]]:
        title = title.strip()
        if not title:
            raise ValidationError("Event title cannot be empty.")
        try:
            start = parse_datetime(start_at)
            end = parse_datetime(end_at) if end_at else start + timedelta(hours=1)
        except DateParseError as exc:
            raise ValidationError(str(exc)) from exc
        if end <= start:
            raise ValidationError("Event end must be after start.")
        conflicts = self.overlapping(start, end)
        now = utc_now()
        row = CalendarEvent(
            id=str(uuid4()),
            title=title,
            start_at=start,
            end_at=end,
            location=location.strip(),
            notes=notes.strip(),
            created_at=now,
            updated_at=now,
        )
        self._session.add(row)
        self._session.flush()
        return _to_record(row), conflicts

    def overlapping(self, start: datetime, end: datetime, *, exclude_id: str | None = None) -> list[CalendarRecord]:
        stmt = select(CalendarEvent).where(
            CalendarEvent.start_at < end, CalendarEvent.end_at > start
        )
        if exclude_id:
            stmt = stmt.where(CalendarEvent.id != exclude_id)
        return [_to_record(row) for row in self._session.scalars(stmt).all()]

    def get(self, event_id: str) -> CalendarRecord:
        row = self._session.get(CalendarEvent, event_id)
        if row is None:
            raise EventNotFoundError(f"No calendar event {event_id!r}.")
        return _to_record(row)

    def list_range(self, start: datetime, end: datetime) -> list[CalendarRecord]:
        stmt = (
            select(CalendarEvent)
            .where(CalendarEvent.start_at < end, CalendarEvent.end_at > start)
            .order_by(CalendarEvent.start_at)
        )
        return [_to_record(row) for row in self._session.scalars(stmt).all()]

    def today(self, *, now: datetime | None = None) -> list[CalendarRecord]:
        moment = now or utc_now()
        start = moment.replace(hour=0, minute=0, second=0, microsecond=0)
        return self.list_range(start, start + timedelta(days=1))

    def delete(self, event_id: str) -> CalendarRecord:
        row = self._session.get(CalendarEvent, event_id)
        if row is None:
            raise EventNotFoundError(f"No calendar event {event_id!r}.")
        record = _to_record(row)
        self._session.delete(row)
        self._session.flush()
        return record
