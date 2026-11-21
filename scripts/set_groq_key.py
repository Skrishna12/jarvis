#!/usr/bin/env python3
"""Write a Groq API key into local .env. Run in a terminal; do not paste the key in chat."""

from __future__ import annotations

from getpass import getpass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / ".env"

GROQ = {
    "JARVIS_LLM_PROVIDER": "openai_compatible",
    "JARVIS_LLM_BASE_URL": "https://api.groq.com/openai/v1",
    "JARVIS_LLM_MODEL": "openai/gpt-oss-120b",
}


def main() -> int:
    key = getpass("Paste Groq API key (it will not echo): ").strip()
    if not key:
        print("No key entered. Nothing changed.")
        return 1
    if ENV.is_file():
        lines = ENV.read_text(encoding="utf-8").splitlines()
    else:
        lines = []
    values = dict(GROQ)
    values["JARVIS_LLM_API_KEY"] = key
    seen: set[str] = set()
    out: list[str] = []
    for line in lines:
        if "=" in line and not line.lstrip().startswith("#"):
            name = line.split("=", 1)[0].strip()
            if name in values:
                out.append(f"{name}={values[name]}")
                seen.add(name)
                continue
        out.append(line)
    for name, value in values.items():
        if name not in seen:
            out.append(f"{name}={value}")
    ENV.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"Saved Groq settings to {ENV} ({len(key)} characters). Key is not printed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
