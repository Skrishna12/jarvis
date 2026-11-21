# Jarvis

Personal CLI assistant: chat orchestrator, tasks, reminders, memory, email,
calendar, projects, local doc search, and **read-only GitHub**.

Email send always waits for confirmation. GitHub tools never write.

Out of scope: voice, mobile, web dashboard, computer control.

## Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
jarvis db upgrade
```

`.env` is gitignored. Defaults (`fake` LLM, email, GitHub) need no accounts.

Groq (paste the key only in `.env`, never in chat):

```
JARVIS_LLM_PROVIDER=openai_compatible
JARVIS_LLM_API_KEY=
JARVIS_LLM_BASE_URL=https://api.groq.com/openai/v1
JARVIS_LLM_MODEL=openai/gpt-oss-120b
```

Real inbox (IMAP/SMTP) — **your** `.env` only, never in chat:

```
JARVIS_EMAIL_BACKEND=imap
JARVIS_EMAIL_ADDRESS=you@gmail.com
JARVIS_EMAIL_PASSWORD=app-password-not-your-login-password
```

Read-only GitHub API (optional):

```
JARVIS_GITHUB_BACKEND=api
JARVIS_GITHUB_TOKEN=your-token-not-in-chat
```

## Everyday commands

```bash
jarvis chat
jarvis briefing morning
jarvis calendar today
jarvis calendar create "Standup" --start 2026-11-21T09:00:00
jarvis project create Launch
jarvis github repos
jarvis docs ingest ./notes.md
jarvis docs search pineapple
jarvis email fetch
jarvis email send <id>          # confirmation required
```

Chat phrases: `morning briefing`, `calendar today`, `list projects`,
`check inbox`, `list tasks`.

## Tests

```bash
pytest
```
