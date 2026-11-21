# Jarvis

Personal CLI assistant: chat orchestrator, tasks, reminders, memory, and
**email** (draft always; send only after you confirm).

Out of scope (later): calendar, GitHub, voice, mobile, RAG, computer control.

## Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
jarvis db upgrade
```

`.env` is gitignored. Default `JARVIS_LLM_PROVIDER=fake` and
`JARVIS_EMAIL_BACKEND=fake` need no accounts.

To use a real inbox (IMAP/SMTP), set in **your** `.env` only — never in chat
or `.env.example`:

```
JARVIS_EMAIL_BACKEND=imap
JARVIS_EMAIL_ADDRESS=you@gmail.com
JARVIS_EMAIL_PASSWORD=app-password-not-your-login-password
```

Gmail: enable 2FA and create an [app password](https://support.google.com/accounts/answer/185833).

## Email

```bash
jarvis email fetch
jarvis email list
jarvis email get <id>
jarvis email summarize <id>
jarvis email draft <id>          # saves a reply, does not send
jarvis email send <id>           # asks for confirmation
jarvis confirm approve <pending-id>
```

Chat: `check inbox`, `list emails`. Send still requires `yes` / confirm.

## Tests

```bash
pytest
```
