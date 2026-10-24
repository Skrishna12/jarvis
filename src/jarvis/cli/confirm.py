from __future__ import annotations

import argparse
import sys

from jarvis.cli.outcome import print_outcome
from jarvis.runtime import app_session
from jarvis.security.confirmations import ConfirmationStore
from jarvis.security.errors import ConfirmationError
from jarvis.security.gate import PermissionGate
from jarvis.tools.catalog import default_registry


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("confirm", help="Approve or deny pending level-2+ actions.")
    sub = parser.add_subparsers(dest="confirm_command", required=True)
    listed = sub.add_parser("list", help="Show pending confirmations.")
    listed.set_defaults(handler=cmd_list)
    approve = sub.add_parser("approve", help="Run a pending action.")
    approve.add_argument("id")
    approve.set_defaults(handler=cmd_approve)
    deny = sub.add_parser("deny", help="Cancel a pending action.")
    deny.add_argument("id")
    deny.set_defaults(handler=cmd_deny)


def cmd_list(_args: argparse.Namespace) -> int:
    with app_session() as (session, _settings):
        rows = ConfirmationStore(session).list_pending()
    if not rows:
        print("(nothing pending)")
        return 0
    for row in rows:
        print(f"{row.id}  L{row.permission_level}  {row.agent}  {row.tool_name}  {row.payload_json}")
    return 0


def cmd_approve(args: argparse.Namespace) -> int:
    return _resolve(args.id, True)


def cmd_deny(args: argparse.Namespace) -> int:
    return _resolve(args.id, False)


def _resolve(confirmation_id: str, approve: bool) -> int:
    try:
        with app_session() as (session, _settings):
            gate = PermissionGate(session, default_registry())
            outcome = gate.resolve(confirmation_id, approve=approve)
    except ConfirmationError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return print_outcome(outcome)
