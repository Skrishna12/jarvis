"""Permission gate: level 0–1 run now; level 2 waits for yes."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from sqlalchemy import select

from jarvis.db.models import ActionLog, PendingConfirmation
from jarvis.security.gate import PermissionGate
from jarvis.security.levels import PermissionLevel
from jarvis.tools.base import Tool, ToolResult
from jarvis.tools.registry import ToolRegistry


class _Stub(Tool):
    def __init__(self, name: str, level: PermissionLevel) -> None:
        self.name = name
        self.description = name
        self.agent = "test"
        self.level = level
        self.calls: list[dict[str, Any]] = []

    def run(self, session: Session, payload: dict[str, Any]) -> ToolResult:
        del session
        self.calls.append(payload)
        return ToolResult(True, f"ran {self.name}", payload)


def _gate(session, *tools: Tool) -> PermissionGate:
    registry = ToolRegistry()
    for tool in tools:
        registry.register(tool)
    return PermissionGate(session, registry)


def test_safe_tool_runs_and_is_logged(db_session) -> None:
    tool = _Stub("safe.ping", PermissionLevel.SAFE)
    gate = _gate(db_session, tool)
    outcome = gate.invoke("safe.ping", {"n": 1}, agent="test")
    assert outcome.status == "ok"
    assert tool.calls == [{"n": 1}]
    logs = list(db_session.scalars(select(ActionLog)).all())
    assert len(logs) == 1
    assert logs[0].result == "ok"
    assert logs[0].permission_level == 1


def test_delete_tool_waits_then_runs_on_approve(db_session) -> None:
    tool = _Stub("task.delete", PermissionLevel.CONFIRM)
    gate = _gate(db_session, tool)
    waiting = gate.invoke("task.delete", {"id": "abc"}, agent="task")
    assert waiting.status == "awaiting_confirmation"
    assert tool.calls == []
    pending = db_session.scalars(select(PendingConfirmation)).one()
    assert pending.status == "pending"

    approved = gate.resolve(waiting.pending_id, approve=True)
    assert approved.status == "ok"
    assert tool.calls == [{"id": "abc"}]


def test_deny_does_not_run_tool(db_session) -> None:
    tool = _Stub("task.delete", PermissionLevel.CONFIRM)
    gate = _gate(db_session, tool)
    waiting = gate.invoke("task.delete", {"id": "abc"})
    denied = gate.resolve(waiting.pending_id, approve=False)
    assert denied.status == "denied"
    assert tool.calls == []
