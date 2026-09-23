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
    assert main(["memory", "get", "USER_PROFILE", "preferred_name"]) == 1
    err = capsys.readouterr().err
    assert "No memory stored" in err


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
