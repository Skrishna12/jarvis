from __future__ import annotations

import argparse
import json
import sys

from jarvis.cli.outcome import print_outcome
from jarvis.runtime import app_session
from jarvis.security.gate import PermissionGate
from jarvis.tools.catalog import default_registry


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("tools", help="List or run permission-gated tools.")
    sub = parser.add_subparsers(dest="tools_command", required=True)
    listed = sub.add_parser("list")
    listed.set_defaults(handler=cmd_list)
    run = sub.add_parser("run")
    run.add_argument("name")
    run.add_argument(
        "--payload",
        default="{}",
        help='JSON object, e.g. {"title":"buy milk"}',
    )
    run.set_defaults(handler=cmd_run)


def cmd_list(_args: argparse.Namespace) -> int:
    for tool in default_registry().all():
        print(f"L{int(tool.level)}  {tool.name:20}  {tool.agent:10}  {tool.description}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    try:
        payload = json.loads(args.payload)
    except json.JSONDecodeError as exc:
        print(f"Payload is not JSON: {exc}", file=sys.stderr)
        return 1
    if not isinstance(payload, dict):
        print("Payload must be a JSON object.", file=sys.stderr)
        return 1
    with app_session() as (session, _settings):
        gate = PermissionGate(session, default_registry())
        outcome = gate.invoke(args.name, payload)
    return print_outcome(outcome)
