#!/usr/bin/env python3
"""Save a Telegram bot token into local .env. Do not paste the token in chat."""

from __future__ import annotations

from getpass import getpass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / ".env"


def main() -> int:
    token = getpass("Paste Telegram bot token (it will not echo): ").strip()
    if not token:
        print("No token entered. Nothing changed.")
        return 1
    if ":" not in token:
        print("That does not look like a BotFather token. It usually contains a colon.")
        return 1
    lines = ENV.read_text(encoding="utf-8").splitlines() if ENV.is_file() else []
    values = {"JARVIS_TELEGRAM_BOT_TOKEN": token}
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
    print(f"Saved Telegram token to {ENV} ({len(token)} characters). Token is not printed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
