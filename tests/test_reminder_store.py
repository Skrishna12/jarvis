from __future__ import annotations

from datetime import datetime, timedelta

from jarvis.core.clock import utc_now
from jarvis.reminders.store import ReminderStore
from jarvis.tasks.store import TaskStore


def test_one_time_due_then_disabled(db_session) -> None:
    store = ReminderStore(db_session)
    past = (utc_now() - timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%S")
    reminder = store.create("Standup", trigger_at=past)
    due = store.due()
    assert due[0].id == reminder.id
    fired = store.mark_fired(reminder.id)
    assert fired.enabled is False
    assert store.due() == []


def test_daily_recurrence_rolls_forward(db_session) -> None:
    store = ReminderStore(db_session)
    when = datetime(2026, 1, 1, 9, 0, 0)
    reminder = store.create(
        "Pills",
        kind="recurring",
        recurrence="daily",
        trigger_at=when.strftime("%Y-%m-%dT%H:%M:%S"),
    )
    fired = store.mark_fired(reminder.id)
    assert fired.enabled is True
    assert fired.trigger_at == datetime(2026, 1, 2, 9, 0, 0)


def test_deadline_can_link_task(db_session) -> None:
    task = TaskStore(db_session).create("Ship MVP")
    reminder = ReminderStore(db_session).create(
        "MVP due",
        kind="deadline",
        trigger_at="2026-12-01T18:00:00",
        task_id=task.id,
    )
    assert reminder.task_id == task.id
