"""Config should load from the process environment without crashing."""

from __future__ import annotations

import os
from pathlib import Path

from jarvis.config import load_settings


def test_load_settings_without_env_file(monkeypatch) -> None:
    monkeypatch.setenv("JARVIS_LLM_API_KEY", "")
    monkeypatch.setenv("JARVIS_LLM_BASE_URL", "https://example.test/v1")
    monkeypatch.setenv("JARVIS_LLM_MODEL", "test-model")

    settings = load_settings(env_file=None)

    assert settings.env_file_loaded is False
    assert settings.llm_api_key == ""
    assert settings.llm_base_url == "https://example.test/v1"
    assert settings.llm_model == "test-model"


def test_load_settings_reads_dotenv_file(tmp_path: Path, monkeypatch) -> None:
    # Isolate from whatever is already in the process environment.
    for key in ("JARVIS_LLM_API_KEY", "JARVIS_LLM_BASE_URL", "JARVIS_LLM_MODEL"):
        monkeypatch.delenv(key, raising=False)

    env_file = tmp_path / ".env"
    env_file.write_text(
        "JARVIS_LLM_API_KEY=placeholder-not-a-real-key\n"
        "JARVIS_LLM_MODEL=from-file\n",
        encoding="utf-8",
    )

    settings = load_settings(env_file=env_file)

    assert settings.env_file_loaded is True
    assert settings.llm_api_key == "placeholder-not-a-real-key"
    assert settings.llm_model == "from-file"


def test_missing_env_file_does_not_crash(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("JARVIS_LLM_API_KEY", raising=False)
    missing = tmp_path / "does-not-exist.env"

    settings = load_settings(env_file=missing)

    assert settings.env_file_loaded is False
    assert settings.llm_api_key == ""
    # Defaults still apply when the file is absent.
    assert settings.llm_model == "gpt-4o-mini"


def test_process_env_wins_over_dotenv_file(tmp_path: Path, monkeypatch) -> None:
    """Do not override a key already set in the shell (override=False)."""
    monkeypatch.setenv("JARVIS_LLM_MODEL", "from-process")
    env_file = tmp_path / ".env"
    env_file.write_text("JARVIS_LLM_MODEL=from-file\n", encoding="utf-8")

    settings = load_settings(env_file=env_file)

    assert settings.llm_model == "from-process"
    assert os.getenv("JARVIS_LLM_MODEL") == "from-process"
