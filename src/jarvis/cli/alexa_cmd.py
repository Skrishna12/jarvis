from __future__ import annotations

import argparse
import sys

from jarvis.alexa.server import serve
from jarvis.runtime import DatabaseNotReadyError, load_ready_settings


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "alexa",
        help="HTTP endpoint for an Alexa skill (Echo speaks Jarvis).",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=39847)
    parser.set_defaults(handler=cmd_alexa)


def cmd_alexa(args: argparse.Namespace) -> int:
    try:
        load_ready_settings()
    except DatabaseNotReadyError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    serve(host=args.host, port=args.port)
    return 0
