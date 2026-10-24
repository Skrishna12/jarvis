from __future__ import annotations


class SecurityError(Exception):
    pass


class ToolNotFoundError(SecurityError):
    pass


class ConfirmationError(SecurityError):
    pass
