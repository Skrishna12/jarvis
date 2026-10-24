"""Provider interface: generate, stream, classify."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator, Sequence

from jarvis.llm.types import ChatMessage, ClassifyResult, GenerateResult


class LLMProvider(ABC):
    """One vendor adapter. Agents should depend on this type, not a brand."""

    @abstractmethod
    def generate(
        self,
        messages: Sequence[ChatMessage],
        *,
        temperature: float = 0.2,
    ) -> GenerateResult:
        """Return a full completion."""

    @abstractmethod
    def stream(
        self,
        messages: Sequence[ChatMessage],
        *,
        temperature: float = 0.2,
    ) -> Iterator[str]:
        """Yield text chunks as they arrive."""

    @abstractmethod
    def classify(
        self,
        text: str,
        labels: Sequence[str],
        *,
        instruction: str | None = None,
    ) -> ClassifyResult:
        """Pick exactly one label from `labels` for `text`."""
