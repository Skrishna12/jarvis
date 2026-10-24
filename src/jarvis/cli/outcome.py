from __future__ import annotations

import sys

from jarvis.security.gate import GateOutcome


def print_outcome(outcome: GateOutcome) -> int:
    stream = sys.stdout if outcome.status in {"ok", "awaiting_confirmation"} else sys.stderr
    print(outcome.message, file=stream)
    if outcome.status == "error":
        return 1
    if outcome.status == "denied":
        return 1
    return 0
