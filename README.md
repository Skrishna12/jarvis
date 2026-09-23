# Jarvis

Personal CLI assistant. This repository is in **Milestone 3 (LLM providers)** —
a vendor-neutral interface (`generate`, `stream`, `classify`) with a fake
provider for tests and an OpenAI-compatible HTTP adapter. There is no agent
routing or chat loop yet.

## Requirements

- Python 3.12+
- A virtual environment (recommended)

## Setup

```bash
cd jarvis
python3.12 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env
```

`.env` is gitignored. Leave `JARVIS_LLM_PROVIDER=fake` and
`JARVIS_LLM_API_KEY` empty unless you want a real API.

Create the database:

```bash
jarvis db upgrade
```

## Run

```bash
python -m jarvis --help
python -m jarvis
jarvis llm generate "hello"
jarvis llm classify "add milk to my list" --labels CHAT,TASK,REMINDER
```

Status prints the provider name and whether an API key is **set** (not the key).

To use OpenAI (or any compatible host: Groq, Ollama, …), in `.env`:

```
JARVIS_LLM_PROVIDER=openai_compatible
JARVIS_LLM_API_KEY=your-key-here
JARVIS_LLM_BASE_URL=https://api.openai.com/v1
JARVIS_LLM_MODEL=gpt-4o-mini
```

Never commit `.env`. Never put a real key in `.env.example`.

## Tests

```bash
pytest
```

Tests use the fake provider and a mocked HTTP client. They do not call a live LLM.

## What is not here yet

Agents, permissions, and the chat loop are later milestones.
See `PROGRESS.md`.
