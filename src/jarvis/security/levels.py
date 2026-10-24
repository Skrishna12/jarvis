from __future__ import annotations

from enum import IntEnum


class PermissionLevel(IntEnum):
    """What a tool is allowed to do without extra checks.

    LEVEL 0 — read only
    LEVEL 1 — safe writes (create a task, remember a preference)
    LEVEL 2 — needs your yes (delete a task)
    LEVEL 3 — highly sensitive (reserved; no default tools use it yet)
    """

    READ = 0
    SAFE = 1
    CONFIRM = 2
    CRITICAL = 3

    @property
    def needs_confirmation(self) -> bool:
        return self >= PermissionLevel.CONFIRM
