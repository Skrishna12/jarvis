"""CLI entry point."""

from __future__ import annotations

import argparse
import sys

from jarvis import __version__
from jarvis.cli import briefing_cmd
from jarvis.cli import calendar_cmd
from jarvis.cli import chat as chat_cmd
from jarvis.cli import confirm as confirm_cmd
from jarvis.cli import conversation as conversation_cmd
from jarvis.cli import database as database_cmd
from jarvis.cli import docs_cmd
from jarvis.cli import email_cmd
from jarvis.cli import github_cmd
from jarvis.cli import llm as llm_cmd
from jarvis.cli import logs as logs_cmd
from jarvis.cli import memory as memory_cmd
from jarvis.cli import commute_cmd
from jarvis.cli import news_cmd
from jarvis.cli import phone_cmd
from jarvis.cli import notify_cmd
from jarvis.cli import project_cmd
from jarvis.cli import reminder_cmd
from jarvis.cli import task_cmd
from jarvis.cli import tools_cmd
from jarvis.cli.status import print_status
from jarvis.runtime import DatabaseNotReadyError
from jarvis.security.errors import SecurityError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="jarvis",
        description="Personal CLI assistant (tasks, calendar, email, GitHub read-only).",
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
    tools_cmd.register(subparsers)
    task_cmd.register(subparsers)
    reminder_cmd.register(subparsers)
    email_cmd.register(subparsers)
    project_cmd.register(subparsers)
    calendar_cmd.register(subparsers)
    github_cmd.register(subparsers)
    docs_cmd.register(subparsers)
    notify_cmd.register(subparsers)
    news_cmd.register(subparsers)
    commute_cmd.register(subparsers)
    phone_cmd.register(subparsers)
    briefing_cmd.register(subparsers)
    confirm_cmd.register(subparsers)
    logs_cmd.register(subparsers)
    chat_cmd.register(subparsers)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    handler = getattr(args, "handler", None)
    if handler is None:
        print_status()
        return 0
    try:
        return handler(args)
    except DatabaseNotReadyError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except SecurityError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
