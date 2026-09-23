"""Provider factory from Settings."""

from __future__ import annotations

import pytest

from jarvis.config import load_settings
from jarvis.llm.errors import LlmConfigError
from jarvis.llm.factory import build_provider
from jarvis.llm.fake import FakeProvider
from jarvis.llm.openai_compatible import OpenAICompatibleProvider


def test_default_provider_is_fake(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("JARVIS_LLM_PROVIDER", raising=False)
    settings = load_settings(env_file=None)
    provider = build_provider(settings)
    assert isinstance(provider, FakeProvider)


def test_openai_compatible_from_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JARVIS_LLM_PROVIDER", "openai_compatible")
    monkeypatch.setenv("JARVIS_LLM_BASE_URL", "https://example.test/v1")
    monkeypatch.setenv("JARVIS_LLM_MODEL", "demo")
    settings = load_settings(env_file=None)
    provider = build_provider(settings)
    assert isinstance(provider, OpenAICompatibleProvider)


def test_unknown_provider_explains_options(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JARVIS_LLM_PROVIDER", "anthropic")
    settings = load_settings(env_file=None)
    with pytest.raises(LlmConfigError, match="openai_compatible"):
        build_provider(settings)
