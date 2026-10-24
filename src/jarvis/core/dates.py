"""Parse the small set of datetime strings we accept from users."""

from __future__ import annotations

from datetime import datetime, timedelta

from jarvis.core.clock import utc_now


class DateParseError(ValueError):
    pass


def parse_datetime(raw: str) -> datetime:
    """Accept ISO-8601 (`2026-10-25T09:00:00`) or a date (`2026-10-25`)."""
    text = raw.strip()
    if not text:
        raise DateParseError("Datetime value cannot be empty.")
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    raise DateParseError(
        f"Could not parse {raw!r} as a datetime. "
        "Use ISO format, e.g. 2026-10-25T09:00:00 or 2026-10-25."
    )


def advance_recurrence(when: datetime, recurrence: str) -> datetime:
    if recurrence == "daily":
        return when + timedelta(days=1)
    if recurrence == "weekly":
        return when + timedelta(weeks=1)
    raise DateParseError(
        f"Unknown recurrence {recurrence!r}. Use daily or weekly."
    )


def ensure_future_or_now(when: datetime) -> datetime:
    """Allow due times in the past (overdue is useful); just return as-is."""
    del when
    return when


def default_trigger() -> datetime:
    return utc_now()
