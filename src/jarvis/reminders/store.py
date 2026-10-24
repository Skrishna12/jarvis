from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from jarvis.core.clock import utc_now
from jarvis.core.dates import advance_recurrence, parse_datetime
from jarvis.db.models import Reminder, Task
from jarvis.memory.errors import ValidationError

KINDS = ("one_time", "recurring", "deadline")
RECURRENCES = ("daily", "weekly")


class ReminderNotFoundError(LookupError):
    pass


@dataclass(frozen=True)
class ReminderRecord:
    id: str
    title: str
    message: str
    kind: str
    trigger_at: datetime
    recurrence: str | None
    task_id: str | None
    enabled: bool
    created_at: datetime
    updated_at: datetime


def _to_record(row: Reminder) -> ReminderRecord:
    return ReminderRecord(
        id=row.id,
        title=row.title,
        message=row.message,
        kind=row.kind,
        trigger_at=row.trigger_at,
        recurrence=row.recurrence,
        task_id=row.task_id,
        enabled=row.enabled,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class ReminderStore:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        title: str,
        *,
        message: str = "",
        kind: str = "one_time",
        trigger_at: str,
        recurrence: str | None = None,
        task_id: str | None = None,
    ) -> ReminderRecord:
        title = title.strip()
        if not title:
            raise ValidationError("Reminder title cannot be empty.")
        kind = kind.strip().lower()
        if kind not in KINDS:
            raise ValidationError(
                f"Unknown reminder kind {kind!r}. Use one of: {', '.join(KINDS)}."
            )
        when = parse_datetime(trigger_at)
        rec: str | None = None
        if kind == "recurring":
            if not recurrence:
                raise ValidationError(
                    "Recurring reminders need recurrence=daily or weekly."
                )
            rec = recurrence.strip().lower()
            if rec not in RECURRENCES:
                raise ValidationError(
                    f"Unknown recurrence {recurrence!r}. Use daily or weekly."
                )
        elif recurrence:
            raise ValidationError(
                "recurrence is only valid when kind=recurring."
            )
        if task_id:
            if self._session.get(Task, task_id) is None:
                raise ValidationError(
                    f"No task {task_id!r} to attach this reminder to."
                )
        now = utc_now()
        row = Reminder(
            id=str(uuid4()),
            title=title,
            message=(message or title).strip(),
            kind=kind,
            trigger_at=when,
            recurrence=rec,
            task_id=task_id or None,
            enabled=True,
            created_at=now,
            updated_at=now,
        )
        self._session.add(row)
        self._session.flush()
        return _to_record(row)

    def get(self, reminder_id: str) -> ReminderRecord:
        row = self._session.get(Reminder, reminder_id)
        if row is None:
            raise ReminderNotFoundError(
                f"No reminder {reminder_id!r}. Use reminder.list to see ids."
            )
        return _to_record(row)

    def list(self, *, enabled_only: bool = False) -> list[ReminderRecord]:
        stmt = select(Reminder).order_by(Reminder.trigger_at)
        if enabled_only:
            stmt = stmt.where(Reminder.enabled.is_(True))
        return [_to_record(row) for row in self._session.scalars(stmt).all()]

    def due(self, *, now: datetime | None = None) -> list[ReminderRecord]:
        moment = now or utc_now()
        stmt = (
            select(Reminder)
            .where(Reminder.enabled.is_(True), Reminder.trigger_at <= moment)
            .order_by(Reminder.trigger_at)
        )
        return [_to_record(row) for row in self._session.scalars(stmt).all()]

    def mark_fired(self, reminder_id: str) -> ReminderRecord:
        """Disable one-time/deadline reminders; roll recurring ones forward."""
        row = self._session.get(Reminder, reminder_id)
        if row is None:
            raise ReminderNotFoundError(
                f"No reminder {reminder_id!r}."
            )
        if row.kind == "recurring" and row.recurrence:
            row.trigger_at = advance_recurrence(row.trigger_at, row.recurrence)
        else:
            row.enabled = False
        row.updated_at = utc_now()
        self._session.flush()
        return _to_record(row)

    def delete(self, reminder_id: str) -> ReminderRecord:
        row = self._session.get(Reminder, reminder_id)
        if row is None:
            raise ReminderNotFoundError(
                f"No reminder {reminder_id!r}."
            )
        record = _to_record(row)
        self._session.delete(row)
        self._session.flush()
        return record
