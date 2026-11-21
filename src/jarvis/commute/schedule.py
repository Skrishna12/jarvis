"""Weekday office hours: leave 09:00, at desk by 09:40, done 18:30 (IST)."""

from __future__ import annotations

from datetime import datetime, timedelta

from jarvis.config import Settings, load_settings
from jarvis.core.clock import local_now
from jarvis.memory.errors import MemoryNotFoundError
from jarvis.memory.store import MemoryStore

_OFFICE_WEEKDAYS = {0, 1, 2, 3, 4}  # Monday–Friday


def is_office_day(when: datetime | None = None, *, tz_name: str | None = None) -> bool:
    moment = when or local_now(tz_name or load_settings().timezone)
    return moment.weekday() in _OFFICE_WEEKDAYS


def resolve_city(session, settings: Settings | None = None) -> str:
    cfg = settings or load_settings()
    if cfg.commute_city:
        return cfg.commute_city
    if session is None:
        return ""
    try:
        return MemoryStore(session).get("USER_PROFILE", "commute_city").value.strip()
    except MemoryNotFoundError:
        return ""


def commute_card(
    *,
    session=None,
    settings: Settings | None = None,
    when: datetime | None = None,
) -> str:
    cfg = settings or load_settings()
    moment = when or local_now(cfg.timezone)
    city = resolve_city(session, cfg)
    city_bit = f" in {city}" if city else ""
    if not is_office_day(moment, tz_name=cfg.timezone):
        return (
            f"Weekend — no office commute today. "
            f"Weekdays you leave at {cfg.commute_leave} to be in by {cfg.commute_arrive}, "
            f"and finish at {cfg.commute_finish}."
        )
    return (
        f"Office day{city_bit}: leave {cfg.commute_leave}, "
        f"at work by {cfg.commute_arrive}, done {cfg.commute_finish} "
        f"({cfg.timezone})."
    )


def next_weekday_at(hour: int, minute: int, *, tz_name: str | None = None) -> datetime:
    """Naive local wall time for the next Mon–Fri at hour:minute."""
    moment = local_now(tz_name or load_settings().timezone)
    candidate = moment.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if candidate <= moment:
        candidate += timedelta(days=1)
    while candidate.weekday() >= 5:
        candidate += timedelta(days=1)
    return candidate.replace(tzinfo=None)


def parse_hhmm(raw: str) -> tuple[int, int]:
    parts = raw.strip().split(":")
    hour = int(parts[0])
    minute = int(parts[1]) if len(parts) > 1 else 0
    return hour, minute
