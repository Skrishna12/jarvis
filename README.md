# Jarvis

Personal CLI assistant. **Phase 1–2** is in: chat orchestrator, task and
reminder agents, permission levels, action log, SQLite memory.

Out of scope (later): email, calendar, GitHub, voice, mobile, RAG, computer
control, proactive suggestions.

## Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
jarvis db upgrade
```

`.env` is gitignored. Default `JARVIS_LLM_PROVIDER=fake` needs no API key.
Set `openai_compatible` and `JARVIS_LLM_API_KEY` only in `.env` if you want a
real model. Never put a real key in `.env.example`.

## Try it

```bash
jarvis chat
# or one shot:
jarvis chat --once "create a task buy milk"
jarvis task list
jarvis reminder create "standup" --at 2026-10-25T09:00:00
jarvis log
```

Deletes need confirmation (level 2):

```bash
jarvis task delete <id>
jarvis confirm list
jarvis confirm approve <pending-id>
# in chat, type yes or no
```

## Tests

```bash
pytest
```

## Conversation summaries

Chat turns are stored in `conversation_messages`. They are **not** automatically
summarized into `memories.CONVERSATION_CONTEXT` — that policy is still open.
