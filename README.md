# Jarvis

Personal CLI assistant: chat orchestrator, tasks, reminders, memory, email,
calendar, projects, local doc search, daily news, and **read-only GitHub**.

Email send always waits for confirmation. GitHub tools never write.

Out of scope: native iOS/Android apps, voice, web dashboard, computer control.
Phone chat is Telegram (`jarvis phone`), not a separate mobile app.

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
jarvis commute city Hyderabad
jarvis commute install
jarvis commute traffic
jarvis news
jarvis briefing morning
jarvis phone                 # Telegram; keep this process running
jarvis alexa                 # Echo speaker; needs ngrok HTTPS + Alexa skill
jarvis calendar today
jarvis calendar create "Standup" --start 2026-11-21T09:00:00
jarvis project create Launch
jarvis github repos
jarvis docs ingest ./notes.md
jarvis docs search pineapple
jarvis email fetch
jarvis email send <id>          # confirmation required
```

Chat phrases: `morning briefing`, `traffic`, `news`, `calendar today`,
`list projects`, `check inbox`, `list tasks`.

Weekdays (Mon–Fri, Asia/Kolkata): leave **09:00**, at work by **09:40**,
finish **18:30**. Morning/evening briefing includes that plus traffic headlines
for `JARVIS_COMMUTE_CITY` (or `commute city Hyderabad` in chat). This is news
about jams/closures, not live Google Maps ETAs.

**Alexa (home Echo):** the speaker is always on, but Jarvis still runs on the
laptop. `jarvis alexa`, then in another terminal `bash scripts/alexa-tunnel.sh`
(no ngrok account). Copy the `https://….trycloudflare.com` URL. In the Alexa
developer console create a custom skill, invocation name `jarvis`, paste
`skills/alexa/interaction-model.json`, set the endpoint to the ngrok https
URL. Say: “Alexa, open Jarvis” or “Alexa, ask Jarvis traffic”. The Echo
cannot wake on the word Jarvis.

**Phone chat:** create a Telegram bot with [@BotFather](https://t.me/BotFather),
put `JARVIS_TELEGRAM_BOT_TOKEN` in `.env` only, then run `jarvis phone` and
leave it running. Message the bot anytime. Confirmations still use yes/no.

Commute is a **bike ride with a helmet intercom**. Morning (about 8:40) and
evening (about 6:25) updates are short spoken calls so they come through
Bluetooth, not a wall of Telegram text.

**Calls:** Jarvis can ring you and *speak* the update (Twilio). Put
`JARVIS_VOICE_BACKEND=twilio`, SID, token, from-number, and `JARVIS_VOICE_TO`
in `.env` only, then `JARVIS_ALERT_CALL=true`. Keep `jarvis phone` running.
Due reminders trigger a call. Morning commute calls only if traffic looks
bad, or if `JARVIS_ALERT_CALL_MORNING=true`. Until Twilio is set, calls stay
**fake** (logged, not dialed).

Morning briefing includes India + world headlines (plus business, tech, sports,
science, health, entertainment) from public RSS. No extra API key. There is no
background daemon yet — run `jarvis briefing morning` each morning, or open
`jarvis chat` (news prints at session start).

## Tests

```bash
pytest
```
