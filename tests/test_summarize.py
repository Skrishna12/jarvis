from __future__ import annotations

from jarvis.agents.orchestrator import Orchestrator
from jarvis.llm.fake import FakeProvider
from jarvis.memory.categories import MemoryCategory
from jarvis.memory.errors import MemoryNotFoundError
from jarvis.memory.store import MemoryStore


def test_summary_writes_after_every_n_messages(db_session) -> None:
    orch = Orchestrator(db_session, FakeProvider(), summary_every=4)

    orch.handle("hello there")
    store = MemoryStore(db_session)
    try:
        store.get(MemoryCategory.CONVERSATION_CONTEXT.value, "latest")
        raised = False
    except MemoryNotFoundError:
        raised = True
    assert raised

    orch.handle("create a task pack bags")
    record = store.get(MemoryCategory.CONVERSATION_CONTEXT.value, "latest")
    assert "pack bags" in record.value or "Recent:" in record.value


def test_second_window_keeps_rolling_summary(db_session) -> None:
    provider = FakeProvider()
    orch = Orchestrator(db_session, provider, summary_every=4)
    orch.handle("create a task alpha")
    orch.handle("create a task beta")
    first = MemoryStore(db_session).get(
        MemoryCategory.CONVERSATION_CONTEXT.value, "latest"
    ).value
    orch.handle("create a task gamma")
    orch.handle("create a task delta")
    second = MemoryStore(db_session).get(
        MemoryCategory.CONVERSATION_CONTEXT.value, "latest"
    ).value
    assert "delta" in second or "gamma" in second
    assert second != first or "alpha" in second
