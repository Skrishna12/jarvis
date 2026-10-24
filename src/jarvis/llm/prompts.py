"""Helpers shared by providers (validation, classify prompt)."""

from __future__ import annotations

from collections.abc import Sequence

from jarvis.llm.errors import LlmConfigError, LlmResponseError
from jarvis.llm.types import ChatMessage


def validate_messages(messages: Sequence[ChatMessage]) -> list[ChatMessage]:
    if not messages:
        raise LlmConfigError(
            "No messages were provided. Pass at least one user message."
        )
    cleaned: list[ChatMessage] = []
    for message in messages:
        role = message.role.strip()
        content = message.content.strip()
        if role not in {"system", "user", "assistant"}:
            raise LlmConfigError(
                f"Unknown chat role {message.role!r}. Use system, user, or assistant."
            )
        if not content:
            raise LlmConfigError("Chat message content cannot be empty.")
        cleaned.append(ChatMessage(role=role, content=content))
    return cleaned


def validate_labels(labels: Sequence[str]) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for raw in labels:
        label = raw.strip()
        if not label:
            raise LlmConfigError("Classification labels cannot be empty.")
        key = label.lower()
        if key in seen:
            raise LlmConfigError(f"Duplicate classification label: {label!r}.")
        seen.add(key)
        cleaned.append(label)
    if len(cleaned) < 2:
        raise LlmConfigError("Classification needs at least two labels to choose from.")
    return cleaned


def classify_prompt(
    text: str,
    labels: Sequence[str],
    instruction: str | None,
) -> list[ChatMessage]:
    label_list = ", ".join(labels)
    extra = f" Extra instruction: {instruction.strip()}" if instruction and instruction.strip() else ""
    system = (
        "You assign the user's text to exactly one label. "
        f"Allowed labels: {label_list}. "
        "Reply with the label only — no punctuation, no explanation."
        f"{extra}"
    )
    return [
        ChatMessage(role="system", content=system),
        ChatMessage(role="user", content=text.strip()),
    ]


def parse_label(raw_text: str, labels: Sequence[str]) -> str:
    """Map model output onto one allowed label (case-insensitive)."""
    candidate = raw_text.strip().strip("\"'`").strip()
    # Take the first line / first token if the model added extra words.
    first = candidate.splitlines()[0].strip() if candidate else ""
    token = first.split()[0] if first else ""
    lookup = {label.lower(): label for label in labels}
    if token.lower() in lookup:
        return lookup[token.lower()]
    if first.lower() in lookup:
        return lookup[first.lower()]
    allowed = ", ".join(labels)
    raise LlmResponseError(
        f"The model replied {raw_text!r}, which is not one of: {allowed}. "
        "Try again, or use a clearer instruction."
    )
