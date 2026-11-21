# Progress

Read this file at the start of every session before changing code.

## Current milestone

**Email agent** (IMAP/SMTP or fake backend). Send is always permission level 2.

## What was built (email)

- Local `emails` cache (SQLite) plus `email.fetch` from a mailbox adapter.
- Default `JARVIS_EMAIL_BACKEND=fake` (in-memory inbox, no network).
- `imap` backend: IMAP fetch + SMTP send; credentials only in `.env`.
- Tools: fetch, list, get, search, classify, summarize, draft, send.
- Categories: Job, Work, Interview, Education, Finance, Bills, Orders,
  Personal, Notifications, Other. Urgency: low / normal / urgent.
- Heuristic classify + ISO-date deadline hints (e.g. interviews).
- **Never sends without confirmation.** Draft is level 1; send is level 2.

## Earlier (Phase 1–2)

Orchestrator, tasks, reminders, memory, permissions, action log, rolling
`CONVERSATION_CONTEXT` summaries, CLI chat.

## Key decisions (email)

- **IMAP/SMTP instead of Gmail OAuth for this slice** — OAuth needs a Google
  Cloud app and a redirect URL. An app password in `.env` is enough for a
  personal CLI. OAuth can replace the transport later without changing tools.
- **Fake backend by default** — tests and first-run never touch a real inbox.
- **Reply goes to `From:`** with subject `Re: …` using the saved draft only.

## Secrets

Email password lives only in local `.env`. Status prints address **set/not
set**, never the password. Action logs already redact `password`.

## What's next

Calendar, then GitHub/projects, RAG, voice — only after you green-light them.
