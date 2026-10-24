"""Task specialist — all writes go through the permission gate."""

from __future__ import annotations

from sqlalchemy.orm import Session

from jarvis.security.gate import GateOutcome, PermissionGate
from jarvis.tools.catalog import default_registry


class TaskAgent:
    def __init__(self, session: Session) -> None:
        self._gate = PermissionGate(session, default_registry())

    def run(self, tool: str, payload: dict) -> GateOutcome:
        return self._gate.invoke(tool, payload, agent="task")
