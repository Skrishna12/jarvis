"""Categorized memory CRUD."""

from __future__ import annotations

import pytest

from jarvis.memory.categories import MemoryCategory
from jarvis.memory.errors import MemoryNotFoundError, ValidationError
from jarvis.memory.store import MemoryStore


def test_upsert_get_and_list(db_session) -> None:
    store = MemoryStore(db_session)
    store.upsert("USER_PROFILE", "preferred_name", "Ada")
    store.upsert("USER_PROFILE", "timezone", "UTC")

    got = store.get("USER_PROFILE", "preferred_name")
    assert got.value == "Ada"
    assert got.category is MemoryCategory.USER_PROFILE

    keys = [row.key for row in store.list("USER_PROFILE")]
    assert keys == ["preferred_name", "timezone"]


def test_upsert_replaces_value_and_keeps_one_row(db_session) -> None:
    store = MemoryStore(db_session)
    first = store.upsert("PREFERENCES", "tone", "brief")
    second = store.upsert("PREFERENCES", "tone", "detailed")

    assert first.id == second.id
    assert store.get("PREFERENCES", "tone").value == "detailed"
    assert len(store.list("PREFERENCES")) == 1


def test_same_key_in_different_categories_is_allowed(db_session) -> None:
    store = MemoryStore(db_session)
    store.upsert("USER_PROFILE", "name", "Ada")
    store.upsert("TASKS", "name", "not a person")

    assert store.get("USER_PROFILE", "name").value == "Ada"
    assert store.get("TASKS", "name").value == "not a person"


def test_delete_missing_key_explains_what_to_do(db_session) -> None:
    store = MemoryStore(db_session)
    with pytest.raises(MemoryNotFoundError, match="no-such"):
        store.delete("USER_PROFILE", "no-such")


def test_delete_removes_row(db_session) -> None:
    store = MemoryStore(db_session)
    store.upsert("CONVERSATION_CONTEXT", "summary", "talked about setup")
    store.delete("CONVERSATION_CONTEXT", "summary")
    with pytest.raises(MemoryNotFoundError):
        store.get("CONVERSATION_CONTEXT", "summary")


def test_unknown_category_is_rejected(db_session) -> None:
    store = MemoryStore(db_session)
    with pytest.raises(ValidationError, match="Unknown memory category"):
        store.upsert("SECRETS", "api", "nope")


def test_empty_key_is_rejected(db_session) -> None:
    store = MemoryStore(db_session)
    with pytest.raises(ValidationError, match="key cannot be empty"):
        store.upsert("USER_PROFILE", "   ", "Ada")
