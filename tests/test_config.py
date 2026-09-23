"""Config should load from the process environment without crashing."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from jarvis.config import load_settings

_LLM_KEYS = (
    "JARVIS_LLM_API_KEY",
    "JARVIS_LLM_BASE_URL",
    "JARVIS_LLM_MODEL",
)


@pytest.fixture(autouse=True)
def clear_llm_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Each test starts without leftover LLM env vars from dotenv or other tests."""
    for key in _LLM_KEYS:
        monkeypatch.delenv(key, raising=False)


def test_load_settings_without_env_file(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JARVIS_LLM_API_KEY", "")
    monkeypatch.setenv("JARVIS_LLM_BASE_URL", "https://example.test/v1")
    monkeypatch.setenv("JARVIS_LLM_MODEL", "test-model")

    settings = load_settings(env_file=None)

    assert settings.env_file_loaded is False
    assert settings.llm_api_key == ""
    assert settings.llm_base_url == "https://example.test/v1"
    assert settings.llm_model == "test-model"


def test_load_settings_reads_dotenv_file(tmp_path: Path) -> None:
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


def test_missing_env_file_does_not_crash(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist.env"

    settings = load_settings(env_file=missing)

    assert settings.env_file_loaded is False
    assert settings.llm_api_key == ""
    assert settings.llm_model == "gpt-4o-mini"


def test_process_env_wins_over_dotenv_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Do not override a key already set in the shell (override=False)."""
    monkeypatch.setenv("JARVIS_LLM_MODEL", "from-process")
    env_file = tmp_path / ".env"
    env_file.write_text("JARVIS_LLM_MODEL=from-file\n", encoding="utf-8")

    settings = load_settings(env_file=env_file)

    assert settings.llm_model == "from-process"
    assert os.getenv("JARVIS_LLM_MODEL") == "from-process"
