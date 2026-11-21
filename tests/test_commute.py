from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from jarvis.agents.orchestrator import Orchestrator
from jarvis.commute.schedule import commute_card, is_office_day
from jarvis.llm.fake import FakeProvider
from jarvis.phone.telegram import handle_update
from jarvis.security.gate import PermissionGate
from jarvis.tools.catalog import default_registry

_IST = ZoneInfo("Asia/Kolkata")


def test_weekdays_are_office_days() -> None:
    monday = datetime(2026, 11, 23, 8, 0, tzinfo=_IST)
    saturday = datetime(2026, 11, 21, 8, 0, tzinfo=_IST)
    assert is_office_day(monday) is True
    assert is_office_day(saturday) is False


def test_commute_card_includes_hours() -> None:
    text = commute_card(when=datetime(2026, 11, 23, 8, 0, tzinfo=_IST))
    assert "09:00" in text
    assert "09:40" in text
    assert "18:30" in text


def test_set_city_and_traffic_tool(db_session) -> None:
    gate = PermissionGate(db_session, default_registry())
    set_city = gate.invoke("commute.set_city", {"city": "Hyderabad"}, agent="commute")
    assert set_city.status == "ok"
    traffic = gate.invoke("commute.traffic", {}, agent="commute")
    assert traffic.status == "ok"
    assert "Jam on the ring road" in traffic.message


def test_chat_traffic_and_telegram_turn(db_session) -> None:
    orch = Orchestrator(db_session, FakeProvider())
    result = orch.handle("traffic")
    assert result.intent == "COMMUTE"
    assert "Jam on the ring road" in result.reply

    chat_id, reply = handle_update(
        orch,
        {"message": {"chat": {"id": 42}, "text": "list tasks"}},
        allow_chat_id="",
    )
    assert chat_id == 42
    assert reply is not None

    locked_id, locked = handle_update(
        orch,
        {"message": {"chat": {"id": 99}, "text": "hello"}},
        allow_chat_id="42",
    )
    assert locked_id == 99
    assert locked is not None
    assert "locked" in locked.lower()
