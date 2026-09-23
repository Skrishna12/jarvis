# Jarvis

Personal CLI assistant. This repository is in **Milestone 1 (foundation)** —
package layout, config from `.env`, and a CLI that prints `--help` / status.
There is no chat loop, database, or LLM calls yet.

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

`.env` is gitignored. Leave `JARVIS_LLM_API_KEY` empty for Milestone 1.
Do not put real keys in `.env.example` or in source files.

## Run

```bash
python -m jarvis --help
python -m jarvis --version
python -m jarvis
# after install, this also works:
jarvis --help
```

You should see a short status line (version, whether `.env` loaded, whether
an API key is set — not the key itself).

## Tests

```bash
pytest
```

## What is not here yet

Agents, SQLite, LLM providers, and the chat loop are later milestones.
See `PROGRESS.md` for what shipped and what comes next.
