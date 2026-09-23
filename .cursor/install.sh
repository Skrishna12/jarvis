#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ ! -d .venv ]]; then
  python3.12 -m venv .venv
fi

.venv/bin/pip install -e ".[dev]"

if [[ ! -f .env ]]; then
  cp .env.example .env
fi
