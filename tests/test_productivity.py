from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from jarvis.agents.orchestrator import Orchestrator
from jarvis.calendar.store import CalendarStore
from jarvis.core.clock import utc_now
from jarvis.docs.store import DocumentStore
from jarvis.llm.fake import FakeProvider
from jarvis.notify.store import NotificationStore
from jarvis.projects.store import ProjectStore
from jarvis.security.gate import PermissionGate
from jarvis.tasks.store import TaskStore
from jarvis.tools.catalog import default_registry


def test_project_and_task_link(db_session) -> None:
    project = ProjectStore(db_session).create("Launch")
    task = TaskStore(db_session).create("Ship docs", project_id=project.id)
    listed = TaskStore(db_session).list(project_id=project.id)
    assert listed[0].id == task.id
    assert listed[0].project_id == project.id


def test_calendar_overlap_creates_notification(db_session) -> None:
    start = utc_now().replace(minute=0, second=0, microsecond=0) + timedelta(hours=2)
    iso = start.strftime("%Y-%m-%dT%H:%M:%S")
    later = (start + timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%S")
    CalendarStore(db_session).create("Standup", iso)
    gate = PermissionGate(db_session, default_registry())
    outcome = gate.invoke(
        "calendar.create",
        {"title": "Overlap", "start_at": later},
        agent="calendar",
    )
    assert outcome.status == "ok"
    assert "overlaps" in outcome.message.lower()
    notices = NotificationStore(db_session).unread()
    assert notices
    assert notices[0].source == "calendar"


def test_docs_ingest_and_search(db_session, tmp_path: Path) -> None:
    path = tmp_path / "notes.md"
    path.write_text("Jarvis stores local notes.\n\nKeyword pineapple appears here.", encoding="utf-8")
    DocumentStore(db_session).ingest(str(path))
    hits = DocumentStore(db_session).search("pineapple")
    assert hits
    assert "pineapple" in hits[0].snippet.lower()


def test_github_fake_via_gate(db_session, monkeypatch) -> None:
    monkeypatch.setenv("JARVIS_GITHUB_BACKEND", "fake")
    gate = PermissionGate(db_session, default_registry())
    repos = gate.invoke("github.repos", {}, agent="github")
    assert repos.status == "ok"
    assert "local/jarvis" in repos.message
    issues = gate.invoke("github.issues", {"repo": "local/jarvis"}, agent="github")
    assert issues.status == "ok"
    assert "Wire calendar" in issues.message


def test_morning_briefing_chat(db_session) -> None:
    ProjectStore(db_session).create("Home")
    start = utc_now().replace(hour=15, minute=0, second=0, microsecond=0)
    CalendarStore(db_session).create("Dentist", start.strftime("%Y-%m-%dT%H:%M:%S"))
    TaskStore(db_session).create("Pay rent", priority="high")
    orch = Orchestrator(db_session, FakeProvider())
    result = orch.handle("morning briefing")
    assert result.intent == "BRIEFING"
    assert "Dentist" in result.reply
    assert "Pay rent" in result.reply
