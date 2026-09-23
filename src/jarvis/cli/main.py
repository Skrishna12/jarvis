"""CLI entry point.

Milestone 3 adds `llm generate|stream|classify`.
The chat loop still arrives in Milestone 7.
"""

from __future__ import annotations

import argparse
import sys

from jarvis import __version__
from jarvis.cli import conversation as conversation_cmd
from jarvis.cli import database as database_cmd
from jarvis.cli import llm as llm_cmd
from jarvis.cli import memory as memory_cmd
from jarvis.cli.status import print_status


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="jarvis",
        description="Personal CLI assistant (Milestone 3: LLM providers).",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"jarvis {__version__}",
    )
    subparsers = parser.add_subparsers(dest="command")
    database_cmd.register(subparsers)
    memory_cmd.register(subparsers)
    conversation_cmd.register(subparsers)
    llm_cmd.register(subparsers)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    handler = getattr(args, "handler", None)
    if handler is None:
        print_status()
        return 0
    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
