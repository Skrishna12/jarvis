"""Install the standard weekday commute reminders once."""

from __future__ import annotations

from jarvis.commute.schedule import next_weekday_at, parse_hhmm
from jarvis.config import load_settings
from jarvis.reminders.store import ReminderStore

LEAVE_TITLE = "Leave for office"
FINISH_TITLE = "Office finishing"


def install_commute_reminders(session) -> list[str]:
    cfg = load_settings()
    store = ReminderStore(session)
    existing = {row.title for row in store.list(enabled_only=True)}
    created: list[str] = []
    leave_h, leave_m = parse_hhmm(cfg.commute_leave)
    # Ping 20 minutes before leaving so there is time to check traffic.
    ping_h, ping_m = _minus_minutes(leave_h, leave_m, 20)
    fin_h, fin_m = parse_hhmm(cfg.commute_finish)
    wrap_h, wrap_m = _minus_minutes(fin_h, fin_m, 5)

    specs = (
        (
            LEAVE_TITLE,
            ping_h,
            ping_m,
            "Check traffic and leave so you are in by "
            f"{cfg.commute_arrive}.",
        ),
        (
            FINISH_TITLE,
            wrap_h,
            wrap_m,
            f"Office wraps at {cfg.commute_finish}. Evening briefing.",
        ),
    )
    for title, hour, minute, message in specs:
        if title in existing:
            continue
        when = next_weekday_at(hour, minute, tz_name=cfg.timezone)
        store.create(
            title,
            message=message,
            kind="recurring",
            recurrence="weekdays",
            trigger_at=when.strftime("%Y-%m-%dT%H:%M:%S"),
        )
        created.append(title)
    return created


def _minus_minutes(hour: int, minute: int, delta: int) -> tuple[int, int]:
    total = hour * 60 + minute - delta
    if total < 0:
        total += 24 * 60
    return total // 60, total % 60
