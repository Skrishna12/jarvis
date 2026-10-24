from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from jarvis.security.levels import PermissionLevel


@dataclass
class ToolResult:
    ok: bool
    message: str
    data: dict[str, Any] = field(default_factory=dict)


class Tool(ABC):
    name: str
    description: str
    agent: str
    level: PermissionLevel

    @abstractmethod
    def run(self, session: Session, payload: dict[str, Any]) -> ToolResult:
        """Execute the action. Validation errors should be raised."""
