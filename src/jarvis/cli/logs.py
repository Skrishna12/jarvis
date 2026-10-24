from __future__ import annotations

import argparse

from jarvis.runtime import app_session
from jarvis.security.action_log import ActionLogger


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("log", help="Show recent tool actions.")
    parser.add_argument("--limit", type=int, default=20)
    parser.set_defaults(handler=cmd_recent)


def cmd_recent(args: argparse.Namespace) -> int:
    with app_session() as (session, _settings):
        rows = ActionLogger(session).recent(limit=args.limit)
    if not rows:
        print("(no actions logged)")
        return 0
    for row in reversed(rows):
        err = f"  {row.error_message}" if row.error_message else ""
        print(
            f"{row.created_at.isoformat()}  {row.result:24}  "
            f"L{row.permission_level}  {row.agent}/{row.action}{err}"
        )
    return 0
