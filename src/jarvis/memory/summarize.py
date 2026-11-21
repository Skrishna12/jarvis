"""Rolling conversation summaries into memories.CONVERSATION_CONTEXT.

Policy (Phase 1–2): run after every N persisted messages (default 10), not
at end of session — `jarvis chat --once` never has a session end. Each run
folds the previous summary plus the latest N turns into key `latest`.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from jarvis.config import load_settings
from jarvis.llm.base import LLMProvider
from jarvis.llm.errors import LlmError
from jarvis.llm.types import ChatMessage
from jarvis.memory.categories import MemoryCategory
from jarvis.memory.conversation import ConversationRecord, ConversationStore
from jarvis.memory.errors import MemoryNotFoundError
from jarvis.memory.store import MemoryStore

CATEGORY = MemoryCategory.CONVERSATION_CONTEXT.value
KEY_SUMMARY = "latest"
KEY_CURSOR = "summarized_message_count"
_MAX_SUMMARY = 2000


class ConversationSummarizer:
    def __init__(
        self,
        session: Session,
        provider: LLMProvider,
        *,
        every: int | None = None,
    ) -> None:
        self._session = session
        self._provider = provider
        self._conversation = ConversationStore(session)
        self._memory = MemoryStore(session)
        self._every = every if every is not None else load_settings().summary_every_messages

    def maybe_run(self) -> str | None:
        """Write/update the rolling summary if enough new messages exist."""
        total = self._conversation.count()
        cursor = self._cursor()
        if total < self._every or total - cursor < self._every:
            return None
        window = self._conversation.recent(limit=self._every)
        previous = self._previous_summary()
        summary = self._compose(previous, window)
        self._memory.upsert(CATEGORY, KEY_SUMMARY, summary)
        self._memory.upsert(CATEGORY, KEY_CURSOR, str(total))
        return summary

    def latest(self) -> str | None:
        try:
            return self._memory.get(CATEGORY, KEY_SUMMARY).value
        except MemoryNotFoundError:
            return None

    def _cursor(self) -> int:
        try:
            raw = self._memory.get(CATEGORY, KEY_CURSOR).value
            return int(raw)
        except (MemoryNotFoundError, ValueError):
            return 0

    def _previous_summary(self) -> str:
        return self.latest() or ""

    def _compose(
        self, previous: str, window: list[ConversationRecord]
    ) -> str:
        extractive = _extractive(previous, window)
        transcript = "\n".join(f"{row.role.value}: {row.content}" for row in window)
        prior = previous.strip() or "(none)"
        try:
            result = self._provider.generate(
                [
                    ChatMessage(
                        role="system",
                        content=(
                            "Summarize this Jarvis conversation for long-term memory. "
                            "Keep facts, tasks, reminders, and preferences. "
                            "Omit secrets, API keys, and passwords if they appear. "
                            "At most 8 short sentences. No markdown."
                        ),
                    ),
                    ChatMessage(
                        role="user",
                        content=(
                            f"Previous summary:\n{prior}\n\n"
                            f"New turns:\n{transcript}"
                        ),
                    ),
                ],
                temperature=0.0,
            )
        except LlmError:
            return extractive
        text = result.text.strip()
        if not text or text.startswith("[fake]"):
            return extractive
        return text[:_MAX_SUMMARY]


def _extractive(previous: str, window: list[ConversationRecord]) -> str:
    users = [row.content.strip() for row in window if row.role.value == "user"]
    recent = "; ".join(users[-5:]) if users else "(no user turns)"
    if previous:
        return f"{previous[:800]}\nRecent: {recent}"[:_MAX_SUMMARY]
    return f"Recent: {recent}"[:_MAX_SUMMARY]
