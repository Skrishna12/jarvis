"""Errors the memory layer raises so callers can explain failures."""

from __future__ import annotations


class MemoryError(Exception):
    """Base class for memory/conversation failures."""


class ValidationError(MemoryError):
    """Input was not acceptable (empty key, unknown category, ...)."""


class MemoryNotFoundError(MemoryError):
    """No row matched the requested category + key."""
