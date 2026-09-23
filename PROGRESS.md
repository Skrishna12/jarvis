# Progress

Read this file at the start of every session before changing code.

## Current milestone

**M1 — Foundation** (complete). Stop here until M1 is explicitly approved.

## What was built (M1)

- Python package under `src/jarvis/` with CLI entry points:
  - `python -m jarvis`
  - console script `jarvis` (after `pip install -e .`)
- Config loader (`jarvis.config`) that reads `.env` via `python-dotenv`
  without requiring an API key yet.
- `.env.example` (placeholders only), `.gitignore` (includes `.env` and
  future SQLite `data/`).
- Tests that load settings from process env and from a temp `.env` file.
- This file and a short README with install/run/test steps.

## Key decisions and why

- **CLI-only for this phase** — web UI / dashboard is out of scope; a
  terminal loop is enough to prove the agent core later.
- **Python 3.12 + src layout** — one language for CLI and agents; `src/`
  avoids accidentally importing an uninstalled tree in a confusing way.
- **Secrets** — real keys live only in a local `.env` that you create.
  This repo never contains a real key. Config prints "set" / "not set",
  never the key value.
- **No empty agent/db/llm packages yet** — those files appear when their
  milestones start, so the tree matches what actually works.
- **LLM env vars exist in `.env.example` but are unused** — so copying
  `.env` now still works when M3 lands; M1 does not call any API.

## Conversation summarization (M7 — not decided)

When we reach the orchestrator/chat loop, **do not invent** when
`conversation_messages` get summarized into
`memories.CONVERSATION_CONTEXT`. Ask first (every N messages vs end of
session vs something else).

## What's next

**M2 — Database + memory** (not started). SQLite, Alembic, memory CRUD,
conversation message store. Do not begin M2 until M1 is explicitly approved.
