"""CLI wiring for db / memory / conversation (uses a temp SQLite file)."""

from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.cli.main import main


@pytest.fixture
def isolated_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    db_path = tmp_path / "cli.db"
    monkeypatch.setenv("JARVIS_DATABASE_PATH", str(db_path))
    return db_path


def test_db_upgrade_and_memory_roundtrip(
    isolated_db: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["db", "upgrade"]) == 0
    assert isolated_db.is_file()
    assert main(["memory", "set", "USER_PROFILE", "preferred_name", "Ada"]) == 0
    assert main(["memory", "get", "USER_PROFILE", "preferred_name"]) == 0
    assert main(["memory", "list", "USER_PROFILE"]) == 0
    out = capsys.readouterr().out
    assert "preferred_name=Ada" in out

    assert main(["memory", "delete", "USER_PROFILE", "preferred_name"]) == 0
    delete_out = capsys.readouterr().out
    assert "permission level 2" in delete_out
    assert main(["memory", "get", "USER_PROFILE", "preferred_name"]) == 0
    still_there = capsys.readouterr().out
    assert "preferred_name=Ada" in still_there

    assert main(["confirm", "list"]) == 0
    pending_line = capsys.readouterr().out.strip().splitlines()[-1]
    pending_id = pending_line.split()[0]
    assert main(["confirm", "approve", pending_id]) == 0
    assert main(["memory", "get", "USER_PROFILE", "preferred_name"]) == 1
    err = capsys.readouterr().err
    assert "No memory stored" in err or "No memory" in err


def test_conversation_add_and_recent(
    isolated_db: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["db", "upgrade"]) == 0
    assert main(["conversation", "add", "user", "hello"]) == 0
    assert main(["conversation", "add", "assistant", "hi"]) == 0
    assert main(["conversation", "recent"]) == 0
    out = capsys.readouterr().out
    assert "user: hello" in out
    assert "assistant: hi" in out


def test_memory_without_database_explains_next_step(
    isolated_db: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["memory", "list", "USER_PROFILE"]) == 1
    err = capsys.readouterr().err
    assert "jarvis db upgrade" in err


def test_help_lists_new_commands(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["--help"])
    assert exit_info.value.code == 0
    out = capsys.readouterr().out
    assert "db" in out
    assert "memory" in out
    assert "conversation" in out
    assert "llm" in out
    assert "chat" in out
    assert "task" in out
    assert "email" in out
    assert "calendar" in out
    assert "github" in out
    assert "briefing" in out
    assert "confirm" in out


def test_llm_generate_and_classify_with_fake(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("JARVIS_LLM_PROVIDER", "fake")
    assert main(["llm", "generate", "hello"]) == 0
    assert main(["llm", "stream", "hello"]) == 0
    assert main(["llm", "classify", "please TASK this", "--labels", "CHAT,TASK"]) == 0
    out = capsys.readouterr().out
    assert "[fake] hello" in out
    assert "TASK" in out


def test_task_create_delete_confirm_and_chat(
    isolated_db: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("JARVIS_LLM_PROVIDER", "fake")
    assert main(["db", "upgrade"]) == 0
    assert main(["task", "create", "buy milk", "--priority", "high"]) == 0
    assert main(["task", "list"]) == 0
    out = capsys.readouterr().out
    assert "buy milk" in out

    assert main(["chat", "--once", "list tasks"]) == 0
    chat_out = capsys.readouterr().out
    assert "buy milk" in chat_out

    assert main(["tools", "run", "task.delete", "--payload", '{"id":"missing"}']) == 0
    waiting = capsys.readouterr().out
    assert "needs your confirmation" in waiting or "permission level 2" in waiting
    assert main(["confirm", "list"]) == 0
    listed = capsys.readouterr().out
    assert "task.delete" in listed


def test_chat_once_prints_due_reminder(
    isolated_db: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("JARVIS_LLM_PROVIDER", "fake")
    assert main(["db", "upgrade"]) == 0
    assert (
        main(
            [
                "reminder",
                "create",
                "overdue ping",
                "--at",
                "2020-01-01T00:00:00",
            ]
        )
        == 0
    )
    capsys.readouterr()
    assert main(["chat", "--once", "list tasks"]) == 0
    out = capsys.readouterr().out
    assert "overdue ping" in out
    assert "Due now" in out


def test_email_fetch_draft_and_confirm_send(
    isolated_db: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from jarvis.email.fake import sample_message, seed_inbox, sent_messages

    monkeypatch.setenv("JARVIS_EMAIL_BACKEND", "fake")
    seed_inbox([sample_message()])
    assert main(["db", "upgrade"]) == 0
    assert main(["email", "fetch"]) == 0
    assert main(["email", "list"]) == 0
    listed = capsys.readouterr().out
    assert "Interview" in listed
    assert main(["chat", "--once", "check inbox"]) == 0
    assert sent_messages() == []


def test_productivity_cli_roundtrip(
    isolated_db: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("JARVIS_LLM_PROVIDER", "fake")
    monkeypatch.setenv("JARVIS_GITHUB_BACKEND", "fake")
    assert main(["db", "upgrade"]) == 0
    assert main(["project", "create", "Launch"]) == 0
    assert main(["calendar", "create", "Standup", "--start", "2026-11-21T09:00:00"]) == 0
    assert main(["github", "repos"]) == 0
    assert main(["briefing", "morning"]) == 0
    assert main(["chat", "--once", "list projects"]) == 0
    out = capsys.readouterr().out
    assert "Launch" in out
    assert "local/jarvis" in out
