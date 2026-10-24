"""Deterministic provider for tests and for running without an API key."""

from __future__ import annotations

from collections.abc import Iterator, Sequence

from jarvis.llm.base import LLMProvider
from jarvis.llm.errors import LlmConfigError
from jarvis.llm.prompts import parse_label, validate_labels, validate_messages
from jarvis.llm.types import ChatMessage, ClassifyResult, GenerateResult

_CHUNK = 12


class FakeProvider(LLMProvider):
    """Does not call the network. Output is derived from the input.

    generate / stream: prefix the last user (or last) message with `[fake]`.
    classify: if the text contains exactly one label (case-insensitive),
    use that; if it contains none, use the first label; if several, error
    so tests can see the ambiguity instead of a silent pick.
    """

    def __init__(self, *, model: str = "fake-model") -> None:
        self.model = model

    def generate(
        self,
        messages: Sequence[ChatMessage],
        *,
        temperature: float = 0.2,
    ) -> GenerateResult:
        del temperature  # Fake output does not use sampling.
        text = _last_content(validate_messages(messages))
        return GenerateResult(
            text=f"[fake] {text}",
            model=self.model,
            provider="fake",
        )

    def stream(
        self,
        messages: Sequence[ChatMessage],
        *,
        temperature: float = 0.2,
    ) -> Iterator[str]:
        full = self.generate(messages, temperature=temperature).text
        for i in range(0, len(full), _CHUNK):
            yield full[i : i + _CHUNK]

    def classify(
        self,
        text: str,
        labels: Sequence[str],
        *,
        instruction: str | None = None,
    ) -> ClassifyResult:
        del instruction
        if not text.strip():
            raise LlmConfigError("Classification text cannot be empty.")
        cleaned = validate_labels(labels)
        haystack = text.lower()
        hits = [label for label in cleaned if label.lower() in haystack]
        if len(hits) == 1:
            label = hits[0]
        elif len(hits) == 0:
            label = cleaned[0]
        else:
            raise LlmConfigError(
                f"Fake classifier found multiple labels in the text ({', '.join(hits)}). "
                "Use only one label name in the sample text."
            )
        # Reuse the same parser so fake and real providers agree on output shape.
        chosen = parse_label(label, cleaned)
        return ClassifyResult(
            label=chosen,
            model=self.model,
            provider="fake",
            raw_text=chosen,
        )


def _last_content(messages: Sequence[ChatMessage]) -> str:
    for message in reversed(messages):
        if message.role == "user":
            return message.content
    return messages[-1].content
