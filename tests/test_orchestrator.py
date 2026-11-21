from __future__ import annotations

from datetime import timedelta

from jarvis.agents.orchestrator import Orchestrator
from jarvis.core.clock import utc_now
from jarvis.llm.fake import FakeProvider
from jarvis.reminders.store import ReminderStore
from jarvis.tasks.store import TaskStore


def test_create_task_via_chat_and_list(db_session) -> None:
    orch = Orchestrator(db_session, FakeProvider())
    created = orch.handle("create a task buy milk")
    assert created.intent == "TASK"
    assert created.outcome is not None
    assert created.outcome.status == "ok"
    tasks = TaskStore(db_session).list()
    assert len(tasks) == 1
    assert tasks[0].title == "buy milk"

    listed = orch.handle("list tasks")
    assert "buy milk" in listed.reply


def test_delete_requires_yes(db_session) -> None:
    orch = Orchestrator(db_session, FakeProvider())
    orch.handle("create a task secret")
    task_id = TaskStore(db_session).list()[0].id
    waiting = orch.handle(f"delete task {task_id}")
    assert waiting.outcome is not None
    assert waiting.outcome.status == "awaiting_confirmation"
    assert TaskStore(db_session).list()  # still there

    denied_path = orch.handle("no")
    assert denied_path.outcome is not None
    assert denied_path.outcome.status == "denied"
    assert TaskStore(db_session).list()

    waiting = orch.handle(f"delete task {task_id}")
    yes = orch.handle("yes")
    assert yes.outcome is not None
    assert yes.outcome.status == "ok"
    assert TaskStore(db_session).list() == []


def test_due_briefing_reports_overdue_and_clears_one_time(db_session) -> None:
    past = (utc_now() - timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%S")
    ReminderStore(db_session).create("Call mom", trigger_at=past)
    orch = Orchestrator(db_session, FakeProvider())
    briefing = orch.due_briefing()
    assert briefing is not None
    assert "Call mom" in briefing
    assert orch.due_briefing() is None
