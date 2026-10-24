"""LLM failures with user-facing explanations (never include secrets)."""

from __future__ import annotations


class LlmError(Exception):
    """Base class for provider and config failures."""


class LlmConfigError(LlmError):
    """Settings are incomplete or invalid."""


class LlmProviderError(LlmError):
    """The remote (or fake) provider could not complete the request."""


class LlmResponseError(LlmError):
    """The provider returned a body we could not use."""
