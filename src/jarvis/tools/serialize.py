from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from enum import Enum
from typing import Any


def record_data(record: Any) -> dict[str, Any]:
    raw = asdict(record)
    return {key: _jsonable(value) for key, value in raw.items()}


def _jsonable(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    return value
