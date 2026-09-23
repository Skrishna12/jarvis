"""CLI entry point.

Milestone 1 only exposes --help / --version and a short status line.
The chat loop arrives in Milestone 7.
"""

from __future__ import annotations

import argparse
import sys

from jarvis import __version__
from jarvis.config import load_settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="jarvis",
        description="Personal CLI assistant (Milestone 1: foundation only).",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"jarvis {__version__}",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    parser.parse_args(argv)

    settings = load_settings()
    key_state = "set" if settings.llm_api_key else "not set"
    env_state = "yes" if settings.env_file_loaded else "no"

    print(f"Jarvis {__version__} — foundation only (Milestone 1).")
    print("Chat, agents, and database are not wired yet.")
    print(f"  .env file loaded: {env_state}")
    print(f"  JARVIS_LLM_API_KEY: {key_state}")
    print(f"  JARVIS_LLM_MODEL: {settings.llm_model}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
