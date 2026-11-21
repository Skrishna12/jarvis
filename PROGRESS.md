# Progress

Read this file at the start of every session before changing code.

## Current milestone

**Productivity pack** — calendar, projects, GitHub (read-only), local doc
search, in-app notifications, morning/evening briefing.

## What was built (this pack)

- `projects` table; tasks may set `project_id`.
- Local `calendar_events` with overlap warnings + a notification.
- `github.repos` / `github.issues` / `github.pulls` — **read-only**. Default
  `JARVIS_GITHUB_BACKEND=fake`. Live API needs a token in local `.env`.
- Local document ingest + keyword search (markdown/text/code, no embeddings).
- Unread `notifications` plus `briefing.morning` / `briefing.evening`.
- Daily news (India + world + topic RSS) in `news.digest` and morning briefing.
- Weekday commute 09:00–09:40 / finish 18:30 (IST) plus traffic RSS.
- Telegram `jarvis phone` so the same orchestrator works from a phone.
- Alexa custom skill endpoint (`jarvis alexa`) so an Echo can speak replies.
- Proactive alerts while `jarvis phone` runs: Telegram ping, optional Twilio
  call that speaks the update (due reminders; commute traffic when urgent).
- CLI: `project`, `calendar`, `github`, `docs`, `notify`, `news`, `commute`,
  `phone`, `briefing`.

## Earlier

Orchestrator, tasks, reminders, memory, permissions, action log, rolling
`CONVERSATION_CONTEXT` summaries, CLI chat, email (IMAP/SMTP or fake; send
always level 2).

## Key decisions

- **GitHub is read-only on purpose.** No comments, merges, or pushes.
- **Docs search is keyword, not embeddings.** Good enough for a personal CLI
  without a vector DB.
- **Calendar is local SQLite**, not Google Calendar OAuth.
- Voice, native mobile apps, web dashboard, and computer control stay out of
  scope. Phone access is Telegram, not an App Store app.

## Secrets

LLM key, email password, and GitHub token live only in local `.env`. Status
prints **set/not set**. Action logs redact `token` / `password` / `api_key`.

## What's next (only if asked)

Voice, mobile, web dashboard, computer control, Gmail OAuth, real embeddings.
