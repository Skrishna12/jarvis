from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from jarvis.memory.store import MemoryStore
from jarvis.security.levels import PermissionLevel
from jarvis.tools.base import Tool, ToolResult
from jarvis.tools.serialize import record_data


class MemoryGetTool(Tool):
    name = "memory.get"
    description = "Read one remembered fact."
    agent = "memory"
    level = PermissionLevel.READ

    def run(self, session: Session, payload: dict[str, Any]) -> ToolResult:
        record = MemoryStore(session).get(payload.get("category", ""), payload.get("key", ""))
        return ToolResult(True, f"{record.key}={record.value}", record_data(record))


class MemoryListTool(Tool):
    name = "memory.list"
    description = "List facts in one category."
    agent = "memory"
    level = PermissionLevel.READ

    def run(self, session: Session, payload: dict[str, Any]) -> ToolResult:
        records = MemoryStore(session).list(payload.get("category", ""))
        if not records:
            return ToolResult(True, f"No memories in {payload.get('category')}.", {"items": []})
        return ToolResult(
            True,
            "; ".join(f"{r.key}={r.value}" for r in records),
            {"items": [record_data(r) for r in records]},
        )


class MemoryUpsertTool(Tool):
    name = "memory.upsert"
    description = "Create or update a remembered fact."
    agent = "memory"
    level = PermissionLevel.SAFE

    def run(self, session: Session, payload: dict[str, Any]) -> ToolResult:
        record = MemoryStore(session).upsert(
            payload.get("category", ""),
            payload.get("key", ""),
            payload.get("value", ""),
        )
        return ToolResult(True, f"Remembered {record.key}.", record_data(record))


class MemoryDeleteTool(Tool):
    name = "memory.delete"
    description = "Forget one fact."
    agent = "memory"
    level = PermissionLevel.CONFIRM

    def run(self, session: Session, payload: dict[str, Any]) -> ToolResult:
        record = MemoryStore(session).delete(
            payload.get("category", ""),
            payload.get("key", ""),
        )
        return ToolResult(True, f"Forgot {record.key}.", record_data(record))
