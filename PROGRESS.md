# Progress

Read this file at the start of every session before changing code.

## Current milestone

**M2 — Database + memory** (complete). Stop here until M2 is explicitly approved.
Do not start M3 until then.

## What was built (M2)

- SQLite file (default `data/jarvis.db`, override with `JARVIS_DATABASE_PATH`).
- SQLAlchemy 2 models: `memories`, `conversation_messages`.
- Alembic migration `001_m2_memory` plus `jarvis db upgrade` / `jarvis db current`.
- `MemoryStore`: create/update (upsert), get, list-by-category, delete.
  Categories: `USER_PROFILE`, `TASKS`, `PREFERENCES`, `CONVERSATION_CONTEXT`.
- `ConversationStore`: append a turn (`user` / `assistant` / `system`) and
  `recent(limit)` (oldest-first window). **No summarization.**
- CLI: `jarvis memory …`, `jarvis conversation …`.
- Tests for stores, migrations, CLI, and config path resolution.

## What was built (M1)

- Python package under `src/jarvis/` with CLI entry points.
- Config loader from `.env`; `.env.example`; `.gitignore`; README.

## Key decisions and why (M2)

- **SQLite + SQLAlchemy + Alembic** — one local file, no database server; models
  in Python; schema changes recorded as migrations instead of ad-hoc SQL.
- **Only memory + conversation tables** — tasks, reminders, action logs, and
  confirmations wait for M4–M6 so this milestone stays testable on its own.
- **Unique `(category, key)`** — setting the same fact twice updates it; the
  same key in two categories is allowed (a TASKS `name` is not a profile name).
- **Explicit `jarvis db upgrade`** — the CLI does not silently create a schema
  on first read, so a missing file is an error with a next step.
- **Timestamps stored as UTC without tzinfo** — SQLite has no timezone type;
  we always write UTC.
- **Conversation store is append-only** — we persist turns so M7 can reload
  them; we do **not** write `CONVERSATION_CONTEXT` summaries yet.

## Key decisions (M1, still in force)

- CLI-only; Python 3.12 src layout; secrets only in local `.env`; no real keys
  in the repo.

## Conversation summarization (M7 — not decided)

When we reach the orchestrator/chat loop, **do not invent** when
`conversation_messages` get summarized into
`memories.CONVERSATION_CONTEXT`. Ask first (every N messages vs end of
session vs something else).

## What's next

**M3 — LLM abstraction** (not started). Interface + OpenAI-compatible provider
+ FakeProvider; `generate` / `stream` / `classify`. No routing yet.
