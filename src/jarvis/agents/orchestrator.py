"""Route a user turn to task/reminder/memory tools, then reply.

Conversation rows are persisted. We do **not** write CONVERSATION_CONTEXT
summaries — that policy is still unapproved.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from jarvis.agents.planner import Plan, plan_from_llm_text, plan_from_text
from jarvis.llm.base import LLMProvider
from jarvis.llm.errors import LlmError
from jarvis.llm.types import ChatMessage
from jarvis.memory.conversation import ConversationStore
from jarvis.security.gate import GateOutcome, PermissionGate
from jarvis.tools.catalog import default_registry

_INTENTS = ("CHAT", "TASK", "REMINDER", "MEMORY", "CONFIRM")
_YES = {"yes", "y", "ok", "okay", "approve", "confirm"}
_NO = {"no", "n", "cancel", "deny", "nope"}


@dataclass
class TurnResult:
    reply: str
    intent: str
    outcome: GateOutcome | None = None


class Orchestrator:
    def __init__(self, session: Session, provider: LLMProvider) -> None:
        self._session = session
        self._provider = provider
        self._gate = PermissionGate(session, default_registry())
        self._conversation = ConversationStore(session)

    def handle(self, user_text: str) -> TurnResult:
        text = user_text.strip()
        if not text:
            return TurnResult("Say something and I'll try to help.", "CHAT")

        self._conversation.add("user", text)

        if text.lower() in _YES or text.lower() in _NO:
            result = self._handle_confirm(text.lower() in _YES)
            self._conversation.add("assistant", result.reply)
            return result

        intent = self._intent(text)
        if intent == "CONFIRM":
            result = self._handle_confirm(True)
            self._conversation.add("assistant", result.reply)
            return result

        if intent == "CHAT":
            reply = self._chat_reply(text)
            self._conversation.add("assistant", reply)
            return TurnResult(reply, "CHAT")

        plan = self._plan(text, intent)
        if plan is None or plan.tool is None:
            reply = plan.reply if plan and plan.reply else (
                "I understood this as "
                f"{intent.lower()}, but I could not tell which action to take. "
                "Try 'list tasks', 'create a task buy milk', or "
                "'remind me standup 2026-10-25T09:00:00'."
            )
            self._conversation.add("assistant", reply)
            return TurnResult(reply, intent)

        outcome = self._gate.invoke(plan.tool, plan.payload, agent=self._agent_for(plan.tool))
        reply = self._format_outcome(outcome)
        self._conversation.add("assistant", reply)
        return TurnResult(reply, intent, outcome)

    def _handle_confirm(self, approve: bool) -> TurnResult:
        pending_id = self._gate.latest_pending_id()
        if pending_id is None:
            return TurnResult("There is nothing waiting for confirmation.", "CONFIRM")
        outcome = self._gate.resolve(pending_id, approve=approve)
        return TurnResult(self._format_outcome(outcome), "CONFIRM", outcome)

    def _intent(self, text: str) -> str:
        lower = text.lower()
        if any(word in lower for word in ("remind", "reminder", "alarm")):
            return "REMINDER"
        if any(word in lower for word in ("task", "todo", "subtask")):
            return "TASK"
        if any(word in lower for word in ("remember", "forget", "preference")):
            return "MEMORY"
        try:
            classified = self._provider.classify(text, _INTENTS)
            if classified.label in _INTENTS:
                return classified.label
        except LlmError:
            pass
        return "CHAT"

    def _plan(self, text: str, intent: str) -> Plan | None:
        heuristic = plan_from_text(text)
        if heuristic is not None:
            return heuristic
        try:
            generated = self._provider.generate(
                [
                    ChatMessage(role="system", content=_planner_prompt(intent)),
                    ChatMessage(role="user", content=text),
                ],
                temperature=0.0,
            )
            parsed = plan_from_llm_text(generated.text)
            if parsed is not None:
                return parsed
        except LlmError:
            pass
        return None

    def _chat_reply(self, text: str) -> str:
        history = self._conversation.recent(limit=12)
        messages = [
            ChatMessage(
                role="system",
                content=(
                    "You are Jarvis, a personal CLI assistant. Be brief. "
                    "You can manage tasks and reminders when asked. "
                    "Do not claim you sent email or changed files."
                ),
            )
        ]
        for row in history[:-1]:
            messages.append(ChatMessage(role=row.role.value, content=row.content))
        messages.append(ChatMessage(role="user", content=text))
        try:
            return self._provider.generate(messages).text
        except LlmError as exc:
            return (
                f"I could not reach the language model: {exc}. "
                "I can still run tools — try 'list tasks'."
            )

    def _agent_for(self, tool_name: str) -> str:
        if tool_name.startswith("task."):
            return "task"
        if tool_name.startswith("reminder."):
            return "reminder"
        if tool_name.startswith("memory."):
            return "memory"
        return "orchestrator"

    def _format_outcome(self, outcome: GateOutcome) -> str:
        return outcome.message


def _planner_prompt(intent: str) -> str:
    return (
        "You are Jarvis's action planner. "
        f"The user's intent looks like {intent}. "
        "Reply with JSON only, no markdown. "
        'Either {"tool":"task.create","payload":{"title":"..."}} '
        'or {"tool":null,"reply":"a clarifying question"}. '
        "Tools: task.list, task.get, task.create, task.update, task.complete, "
        "task.prioritize, task.add_subtask, task.delete, reminder.list, "
        "reminder.due, reminder.create, reminder.delete, memory.get, "
        "memory.list, memory.upsert, memory.delete. "
        "task.create payload: title, optional description, priority, due_at. "
        "reminder.create payload: title, trigger_at (ISO datetime), optional "
        "kind (one_time|recurring|deadline), recurrence (daily|weekly), message."
    )
