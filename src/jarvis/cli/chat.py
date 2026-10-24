"""Interactive chat loop (Milestone 7)."""

from __future__ import annotations

import argparse
import sys

from jarvis.agents.orchestrator import Orchestrator
from jarvis.llm.errors import LlmError
from jarvis.llm.factory import build_provider
from jarvis.runtime import DatabaseNotReadyError, app_session


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("chat", help="Talk to Jarvis (orchestrator loop).")
    parser.add_argument(
        "--once",
        dest="once",
        default="",
        help="Send one message and exit (useful in tests).",
    )
    parser.set_defaults(handler=cmd_chat)


def cmd_chat(args: argparse.Namespace) -> int:
    if args.once:
        return _one_turn(args.once)
    print("Jarvis chat. Type quit to exit, yes/no to confirm pending actions.")
    try:
        while True:
            try:
                line = input("> ")
            except EOFError:
                print()
                return 0
            if line.strip().lower() in {"quit", "exit", "q"}:
                return 0
            code = _one_turn(line)
            if code != 0 and line.strip() == "":
                continue
    except DatabaseNotReadyError as exc:
        print(str(exc), file=sys.stderr)
        return 1


def _one_turn(text: str) -> int:
    try:
        with app_session() as (session, settings):
            provider = build_provider(settings)
            result = Orchestrator(session, provider).handle(text)
            print(result.reply)
            return 0
    except DatabaseNotReadyError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except LlmError as exc:
        print(str(exc), file=sys.stderr)
        return 1
