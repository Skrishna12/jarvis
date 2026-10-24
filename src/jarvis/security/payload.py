"""JSON helpers that never log obvious secret field names."""

from __future__ import annotations

import json
from typing import Any

_REDACT_KEYS = {"api_key", "token", "password", "secret", "authorization"}


def dumps(payload: dict[str, Any]) -> str:
    return json.dumps(_redact(payload), sort_keys=True)


def loads(raw: str) -> dict[str, Any]:
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("Payload JSON must be an object.")
    return data


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            if str(key).lower() in _REDACT_KEYS:
                out[key] = "[redacted]"
            else:
                out[key] = _redact(item)
        return out
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value
