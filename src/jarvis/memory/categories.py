"""Allowed memory categories for this phase."""

from __future__ import annotations

from enum import StrEnum


class MemoryCategory(StrEnum):
    USER_PROFILE = "USER_PROFILE"
    TASKS = "TASKS"
    PREFERENCES = "PREFERENCES"
    CONVERSATION_CONTEXT = "CONVERSATION_CONTEXT"
