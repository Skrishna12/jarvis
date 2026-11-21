"""Weekday office hours: leave 09:00, at desk by 09:40, done 18:30 (IST)."""

from __future__ import annotations

from datetime import datetime

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
