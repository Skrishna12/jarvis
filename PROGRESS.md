# Progress

Read this file at the start of every session before changing code.

## Current milestone

**M3 — LLM abstraction** (complete). Stop here until M3 is explicitly approved.
Do not start M4 until then.

## What was built (M3)

- `LLMProvider` interface: `generate()`, `stream()`, `classify()`.
- `FakeProvider` — no network; used by default and in tests.
- `OpenAICompatibleProvider` — HTTP Chat Completions via `httpx` (OpenAI, Groq,
  many local servers). Not an official vendor SDK, so the host is a URL change.
- `build_provider(settings)` from `JARVIS_LLM_PROVIDER`.
- CLI: `jarvis llm generate|stream|classify`.
- Errors explain HTTP 401/404/429/timeouts **without** printing the API key.

## What was built (M2)

- SQLite, Alembic, `MemoryStore`, `ConversationStore`, related CLI.

## What was built (M1)

- Package layout, dotenv config, CLI entry points.

## Key decisions and why (M3)

- **Default provider is `fake`** — you can test the CLI without creating a
  vendor account. Switch to `openai_compatible` in `.env` when you have a key.
- **Raw HTTP instead of the OpenAI Python SDK** — one adapter covers any
  OpenAI-compatible `/v1/chat/completions` host. A later Anthropic adapter
  would be a new file that still implements `LLMProvider`.
- **`classify()` is a constrained generate** — the model must reply with one
  of the given labels; we reject anything else instead of guessing.
- **Fake classify is deterministic** — if the sample text contains exactly one
  label name, that label wins; if none, the first label; if several, error.
  That keeps tests honest without a silent fallback when the input is messy.
- **Secrets** — still only in local `.env`. HTTP 401 messages tell you to check
  the key, never echo it.

## Key decisions still in force

- CLI-only; Python 3.12; SQLite; no real keys in the repo.
- Only memory + conversation tables so far.

## Conversation summarization (M7 — not decided)

When we reach the orchestrator/chat loop, **do not invent** when
`conversation_messages` get summarized into
`memories.CONVERSATION_CONTEXT`. Ask first.

## What's next

**M4 — Permissions + action log** (not started). Levels 0–3 gate, confirmation
prompt, every tool call logged. No task/reminder business logic yet.
