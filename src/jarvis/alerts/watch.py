"""Proactive pings: Telegram message, and a phone call when it is urgent."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from jarvis.commute.schedule import commute_card, is_office_day
from jarvis.commute.traffic import fetch_traffic, format_traffic
from jarvis.config import Settings, load_settings
from jarvis.core.clock import local_now
from jarvis.memory.errors import MemoryNotFoundError
from jarvis.memory.store import MemoryStore
from jarvis.notify.store import NotificationStore
from jarvis.reminders.store import ReminderStore
from jarvis.voice.gateway import VoiceGateway

_TRAFFIC_HIT = (
    "jam",
    "jams",
    "closed",
    "closure",
    "waterlog",
    "flood",
    "diversion",
    "accident",
    "delay",
    "delayed",
    "strike",
    "blocked",
    "snarl",
)


@dataclass(frozen=True)
class Alert:
    kind: str
    title: str
    body: str
    call: bool


def collect_alerts(
    session: Session,
    settings: Settings | None = None,
    *,
    now: datetime | None = None,
) -> list[Alert]:
    cfg = settings or load_settings()
    moment = now or local_now(cfg.timezone)
    alerts: list[Alert] = []
    memory = MemoryStore(session)

    due = ReminderStore(session).due()
    if due:
        titles = ", ".join(r.title for r in due)
        spoken = f"Jarvis here. These reminders are due: {titles}."
        alerts.append(Alert("due", "Reminders due", spoken, call=True))
        for row in due:
            ReminderStore(session).mark_fired(row.id)

    if is_office_day(moment, tz_name=cfg.timezone):
        if _in_morning_window(moment, cfg) and _once(memory, "last_morning_push", moment):
            traffic = fetch_traffic(session=session)
            urgent = _traffic_urgent(traffic)
            body = commute_card(session=session, settings=cfg, when=moment)
            body += "\n" + format_traffic(traffic)
            spoken = "Jarvis here. Office commute update. " + body.replace("\n", ". ")
            alerts.append(Alert("morning", "Morning commute", spoken, call=urgent or cfg.alert_call_morning))
        if _in_evening_window(moment, cfg) and _once(memory, "last_evening_push", moment):
            body = commute_card(session=session, settings=cfg, when=moment)
            spoken = f"Jarvis here. Office finishes at {cfg.commute_finish}. {body}"
            alerts.append(Alert("evening", "Evening wrap", spoken, call=False))

    return alerts


def deliver_alerts(
    session: Session,
    alerts: list[Alert],
    *,
    settings: Settings | None = None,
    telegram=None,
) -> list[str]:
    cfg = settings or load_settings()
    voice = VoiceGateway(cfg)
    notes: list[str] = []
    store = NotificationStore(session)
    chat_id = cfg.telegram_chat_id or _saved_chat_id(session)
    for alert in alerts:
        store.add("alert", alert.title, alert.body)
        if telegram is not None and chat_id:
            telegram.send_message(chat_id, alert.body)
        if alert.call and cfg.alert_call:
            result = voice.speak(alert.body, call=True)
            notes.append(f"called:{result.backend}")
        else:
            voice.speak(alert.body, call=False)
            notes.append("logged")
    return notes


def _saved_chat_id(session: Session) -> str:
    try:
        return MemoryStore(session).get("PREFERENCES", "telegram_chat_id").value
    except MemoryNotFoundError:
        return ""


def _once(memory: MemoryStore, key: str, moment: datetime) -> bool:
    stamp = moment.date().isoformat()
    try:
        if memory.get("PREFERENCES", key).value == stamp:
            return False
    except MemoryNotFoundError:
        pass
    memory.upsert("PREFERENCES", key, stamp)
    return True


def _hhmm(raw: str) -> tuple[int, int]:
    parts = raw.strip().split(":")
    return int(parts[0]), int(parts[1]) if len(parts) > 1 else 0


def _minutes(hour: int, minute: int) -> int:
    return hour * 60 + minute


def _in_morning_window(moment: datetime, cfg: Settings) -> bool:
    leave_h, leave_m = _hhmm(cfg.commute_leave)
    start = _minutes(leave_h, leave_m) - 40
    arrive_h, arrive_m = _hhmm(cfg.commute_arrive)
    end = _minutes(arrive_h, arrive_m)
    now = _minutes(moment.hour, moment.minute)
    return start <= now <= end


def _in_evening_window(moment: datetime, cfg: Settings) -> bool:
    fin_h, fin_m = _hhmm(cfg.commute_finish)
    start = _minutes(fin_h, fin_m) - 15
    end = _minutes(fin_h, fin_m) + 15
    now = _minutes(moment.hour, moment.minute)
    return start <= now <= end


def _traffic_urgent(section) -> bool:
    blob = " ".join(h.title.lower() for h in section.headlines)
    if section.error:
        return False
    return any(word in blob for word in _TRAFFIC_HIT)
