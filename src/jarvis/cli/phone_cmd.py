from __future__ import annotations

import argparse
import sys

from jarvis.memory.errors import ValidationError
from jarvis.phone.telegram import run_forever
from jarvis.runtime import load_ready_settings


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "phone",
        help="Talk to Jarvis from Telegram on your phone (keeps running).",
    )
    parser.set_defaults(handler=cmd_phone)


def cmd_phone(_args: argparse.Namespace) -> int:
    try:
        settings = load_ready_settings()
        run_forever(settings)
        return 0
    except KeyboardInterrupt:
        print()
        return 0
    except ValidationError as exc:
        print(str(exc), file=sys.stderr)
        return 1
