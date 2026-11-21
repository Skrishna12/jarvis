from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from jarvis.alerts.watch import collect_alerts, deliver_alerts
from jarvis.config import load_settings
from jarvis.core.clock import utc_now
from jarvis.reminders.store import ReminderStore
from jarvis.voice.gateway import fake_calls, reset_fake_calls

_IST = ZoneInfo("Asia/Kolkata")


def test_due_reminder_becomes_call_alert(db_session) -> None:
    reset_fake_calls()
    past = (utc_now() - timedelta(minutes=3)).strftime("%Y-%m-%dT%H:%M:%S")
    ReminderStore(db_session).create("Drink water", trigger_at=past)
    alerts = collect_alerts(
        db_session,
        load_settings(env_file=None),
        now=datetime(2026, 11, 23, 10, 0, tzinfo=_IST),
    )
    assert any(a.kind == "due" and "Drink water" in a.body for a in alerts)
    assert ReminderStore(db_session).due() == []


def test_weekday_morning_commute_alert_once(db_session) -> None:
    settings = load_settings(env_file=None)
    morning = datetime(2026, 11, 23, 8, 30, tzinfo=_IST)
    first = collect_alerts(db_session, settings, now=morning)
    kinds = [a.kind for a in first]
    assert "morning" in kinds
    second = collect_alerts(db_session, settings, now=morning)
    assert "morning" not in [a.kind for a in second]


def test_fake_voice_logs_speech_without_dialing(db_session) -> None:
    reset_fake_calls()
    from jarvis.alerts.watch import Alert

    settings = load_settings(env_file=None)
    deliver_alerts(
        db_session,
        [Alert("manual", "Ping", "Jarvis checking in.", call=True)],
        settings=settings,
    )
    assert fake_calls()
    assert "Jarvis checking in." in fake_calls()[-1]
