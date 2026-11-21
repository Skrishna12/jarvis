from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def utc_now() -> datetime:
    """UTC timestamp stored naive — SQLite has no timezone type."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def local_now(tz_name: str = "Asia/Kolkata") -> datetime:
    """Wall-clock time in the user's timezone (aware)."""
    try:
        zone = ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        zone = ZoneInfo("Asia/Kolkata")
    return datetime.now(zone)
