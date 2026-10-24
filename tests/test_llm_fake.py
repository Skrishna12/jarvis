"""FakeProvider — no network."""

from __future__ import annotations

import pytest

from jarvis.llm.errors import LlmConfigError
from jarvis.llm.fake import FakeProvider
from jarvis.llm.types import ChatMessage


def test_generate_and_stream_echo_last_user() -> None:
    provider = FakeProvider(model="unit-fake")
    messages = [
        ChatMessage(role="system", content="be brief"),
        ChatMessage(role="user", content="hello world"),
    ]
    result = provider.generate(messages)
    assert result.provider == "fake"
    assert result.model == "unit-fake"
    assert result.text == "[fake] hello world"
    assert "".join(provider.stream(messages)) == result.text


def test_classify_picks_label_mentioned_in_text() -> None:
    provider = FakeProvider()
    result = provider.classify("Please create a TASK for me", ["CHAT", "TASK", "REMINDER"])
    assert result.label == "TASK"


def test_classify_falls_back_to_first_label() -> None:
    provider = FakeProvider()
    result = provider.classify("good morning", ["CHAT", "TASK"])
    assert result.label == "CHAT"


def test_classify_rejects_ambiguous_text() -> None:
    provider = FakeProvider()
    with pytest.raises(LlmConfigError, match="multiple labels"):
        provider.classify("TASK and REMINDER", ["TASK", "REMINDER"])


def test_empty_messages_are_rejected() -> None:
    provider = FakeProvider()
    with pytest.raises(LlmConfigError, match="No messages"):
        provider.generate([])
