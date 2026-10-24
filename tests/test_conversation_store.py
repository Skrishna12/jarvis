"""Persisted conversation turns (no summarization)."""

from __future__ import annotations

import pytest

from jarvis.memory.conversation import ConversationStore, MessageRole
from jarvis.memory.errors import ValidationError


def test_add_and_recent_oldest_first(db_session) -> None:
    store = ConversationStore(db_session)
    store.add("user", "hello")
    store.add("assistant", "hi there")
    store.add("system", "keep it short")

    rows = store.recent(limit=10)
    assert [row.role for row in rows] == [
        MessageRole.USER,
        MessageRole.ASSISTANT,
        MessageRole.SYSTEM,
    ]
    assert rows[0].content == "hello"


def test_recent_limit_returns_the_newest_window(db_session) -> None:
    store = ConversationStore(db_session)
    for i in range(5):
        store.add("user", f"m{i}")

    rows = store.recent(limit=2)
    assert [row.content for row in rows] == ["m3", "m4"]


def test_empty_content_and_bad_role_are_rejected(db_session) -> None:
    store = ConversationStore(db_session)
    with pytest.raises(ValidationError, match="content cannot be empty"):
        store.add("user", "   ")
    with pytest.raises(ValidationError, match="Unknown message role"):
        store.add("narrator", "once upon a time")
