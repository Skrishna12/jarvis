"""Run a tool only after its permission level is satisfied."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from sqlalchemy.orm import Session

from jarvis.security.action_log import ActionLogger
from jarvis.security.confirmations import (
    STATUS_APPROVED,
    STATUS_DENIED,
    ConfirmationStore,
)
from jarvis.security.errors import ConfirmationError, ToolNotFoundError
from jarvis.security.levels import PermissionLevel
from jarvis.tools.base import ToolResult
from jarvis.tools.registry import ToolRegistry

GateStatus = Literal["ok", "awaiting_confirmation", "denied", "error"]


@dataclass
class GateOutcome:
    status: GateStatus
    message: str
    data: dict[str, Any] = field(default_factory=dict)
    pending_id: str | None = None
    log_id: str | None = None
    tool_name: str | None = None
    level: int | None = None


class PermissionGate:
    def __init__(self, session: Session, registry: ToolRegistry) -> None:
        self._session = session
        self._registry = registry
        self._log = ActionLogger(session)
        self._confirmations = ConfirmationStore(session)

    def invoke(
        self,
        tool_name: str,
        payload: dict[str, Any] | None,
        *,
        agent: str | None = None,
    ) -> GateOutcome:
        payload = payload or {}
        try:
            tool = self._registry.get(tool_name)
        except ToolNotFoundError as exc:
            log = self._log.record(
                agent=agent or "unknown",
                action=tool_name,
                level=PermissionLevel.READ,
                payload=payload,
                result="error",
                error_message=str(exc),
            )
            return GateOutcome(
                status="error",
                message=str(exc),
                log_id=log.id,
                tool_name=tool_name,
            )

        actor = agent or tool.agent
        if tool.level.needs_confirmation:
            pending = self._confirmations.create(
                tool_name=tool.name,
                payload=payload,
                level=tool.level,
                agent=actor,
            )
            log = self._log.record(
                agent=actor,
                action=tool.name,
                level=tool.level,
                payload=payload,
                result="awaiting_confirmation",
            )
            who = "your confirmation"
            if tool.level is PermissionLevel.CRITICAL:
                who = "your confirmation (level 3 — highly sensitive)"
            return GateOutcome(
                status="awaiting_confirmation",
                message=(
                    f"{tool.name} is permission level {int(tool.level)} and needs {who}. "
                    f"Approve with `jarvis confirm approve {pending.id}` "
                    f"or deny with `jarvis confirm deny {pending.id}`. "
                    "In chat, type yes or no."
                ),
                data={"payload": payload},
                pending_id=pending.id,
                log_id=log.id,
                tool_name=tool.name,
                level=int(tool.level),
            )

        return self._run(tool, payload, actor)

    def resolve(self, confirmation_id: str, *, approve: bool) -> GateOutcome:
        pending = self._confirmations.get(confirmation_id)
        if pending.status != "pending":
            raise ConfirmationError(
                f"Confirmation {confirmation_id} is already {pending.status}."
            )
        payload = self._confirmations.payload(pending)
        if not approve:
            self._confirmations.mark(confirmation_id, STATUS_DENIED)
            log = self._log.record(
                agent=pending.agent,
                action=pending.tool_name,
                level=PermissionLevel(pending.permission_level),
                payload=payload,
                result="denied",
            )
            return GateOutcome(
                status="denied",
                message=f"Cancelled {pending.tool_name}.",
                pending_id=pending.id,
                log_id=log.id,
                tool_name=pending.tool_name,
                level=pending.permission_level,
            )

        tool = self._registry.get(pending.tool_name)
        self._confirmations.mark(confirmation_id, STATUS_APPROVED)
        return self._run(tool, payload, pending.agent, pending_id=pending.id)

    def latest_pending_id(self) -> str | None:
        row = self._confirmations.latest_pending()
        return None if row is None else row.id

    def _run(
        self,
        tool,
        payload: dict[str, Any],
        actor: str,
        *,
        pending_id: str | None = None,
    ) -> GateOutcome:
        try:
            result: ToolResult = tool.run(self._session, payload)
        except Exception as exc:
            log = self._log.record(
                agent=actor,
                action=tool.name,
                level=tool.level,
                payload=payload,
                result="error",
                error_message=str(exc),
            )
            return GateOutcome(
                status="error",
                message=str(exc),
                log_id=log.id,
                pending_id=pending_id,
                tool_name=tool.name,
                level=int(tool.level),
            )

        log = self._log.record(
            agent=actor,
            action=tool.name,
            level=tool.level,
            payload=payload,
            result="ok" if result.ok else "error",
            error_message=None if result.ok else result.message,
        )
        return GateOutcome(
            status="ok" if result.ok else "error",
            message=result.message,
            data=result.data,
            log_id=log.id,
            pending_id=pending_id,
            tool_name=tool.name,
            level=int(tool.level),
        )
