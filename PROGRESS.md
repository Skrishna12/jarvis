# Progress

Read this file at the start of every session before changing code.

## Current milestone

**Phase 1–2 + hardening** (complete for this brief). Chat due briefing and
gated memory CLI are in. Email/calendar/GitHub/voice/RAG remain out of scope.

## What was built (M4–M7)

- Permission levels 0–3. Tools declare a level. Level 2+ stores a pending
  confirmation and waits for `yes` / `jarvis confirm approve`.
- `action_logs` for every tool attempt (timestamp, agent, action, level,
  redacted payload, result).
- Task agent/tools: create, update, complete, prioritize, subtasks, delete.
- Reminder agent/tools: one-time, recurring (`daily`/`weekly`), deadline
  (optional task link), due-check that rolls recurring times forward.
- Orchestrator: heuristic intent + rule planner (works with FakeProvider) and
  JSON planner when a real LLM replies with a tool object.
- `jarvis chat` loop; conversation rows persisted; **no auto-summarization**.

## What was built (M1–M3)

- Package, dotenv config, SQLite memory/conversation, LLM interface
  (`generate` / `stream` / `classify`), Fake + OpenAI-compatible providers.

## Key decisions (M4–M7)

- **`jarvis memory` uses the permission gate** — set is level 1; delete is
  level 2 and needs confirmation (same as chat/tools). There is no ungated
  delete path in the CLI.
- **Chat due briefing** — starting `jarvis chat` (including `--once`) runs
  `reminder.due` and prints overdue items if any. One-time reminders are
  marked fired; recurring ones roll forward. No background daemon.
- **Heuristic planner + LLM JSON** — FakeProvider cannot emit tool JSON, so
  obvious phrases (`create a task …`) are parsed locally. A real model can
  still return `{"tool","payload"}`.
- **No CONVERSATION_CONTEXT summaries** — you asked not to invent the
  schedule. Chat reloads the last ~12 raw turns only.
- **Level 3 reserved** — the gate treats it like level 2 (must confirm). No
  default tool is registered at level 3.
- **Secrets** — still only in `.env`. Action logs redact keys named
  api_key/token/password/secret/authorization.

## Conversation summarization (still not decided)

Ask before writing summaries into `memories.CONVERSATION_CONTEXT`
(every N messages vs end of session vs something else).

## What's next

Still not decided: conversation summarization into `CONVERSATION_CONTEXT`.

Later phases from the long-term vision (email, calendar, GitHub, RAG, voice)
only after an explicit green light and a brief update.
