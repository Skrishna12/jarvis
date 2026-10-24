from __future__ import annotations

import pytest

from jarvis.memory.errors import ValidationError
from jarvis.tasks.store import TaskNotFoundError, TaskStore


def test_create_subtask_complete_and_delete(db_session) -> None:
    store = TaskStore(db_session)
    parent = store.create("Write brief", priority="high")
    child = store.add_subtask(parent.id, "Outline sections")
    assert child.parent_id == parent.id

    store.complete(child.id)
    assert store.get(child.id).status == "done"

    with pytest.raises(ValidationError, match="subtask"):
        store.delete(parent.id)

    store.delete(child.id)
    store.delete(parent.id)
    with pytest.raises(TaskNotFoundError):
        store.get(parent.id)


def test_prioritize_rejects_unknown_value(db_session) -> None:
    store = TaskStore(db_session)
    task = store.create("X")
    with pytest.raises(ValidationError, match="priority"):
        store.prioritize(task.id, "urgent")
