from __future__ import annotations

from datetime import datetime, timezone


def utc_now() -> datetime:
    """UTC timestamp stored naive — SQLite has no timezone type."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
