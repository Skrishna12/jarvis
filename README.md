# Jarvis

Personal CLI assistant. This repository is in **Milestone 2 (database + memory)** —
SQLite persistence for categorized facts and conversation turns. There is no
chat loop, agents, or LLM calls yet.

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

`.env` is gitignored. Leave `JARVIS_LLM_API_KEY` empty. Optionally set
`JARVIS_DATABASE_PATH` (default: `data/jarvis.db` under the repo root).
Do not put real keys in `.env.example` or in source files.

Create the database (this writes `data/jarvis.db`, which is gitignored):

```bash
jarvis db upgrade
```

## Run

```bash
python -m jarvis --help
python -m jarvis --version
python -m jarvis
jarvis db current
```

Status prints whether `.env` loaded, whether an API key is **set** (not the
key), and the database path/revision.

## Tests

```bash
pytest
```

## What is not here yet

Agents, LLM providers, permissions, and the chat loop are later milestones.
See `PROGRESS.md` for what shipped and what comes next.
