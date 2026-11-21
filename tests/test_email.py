from __future__ import annotations

from jarvis.email.categories import EmailCategory, EmailUrgency
from jarvis.email.fake import reset_fake_mailbox, sample_message, seed_inbox, sent_messages
from jarvis.security.gate import PermissionGate
from jarvis.tools.catalog import default_registry


def _gate(session) -> PermissionGate:
    return PermissionGate(session, default_registry())


def test_fetch_classifies_interview_and_deadline(db_session) -> None:
    reset_fake_mailbox()
    seed_inbox([sample_message()])
    gate = _gate(db_session)
    fetched = gate.invoke("email.fetch", {"limit": 5}, agent="email")
    assert fetched.status == "ok"
    item = fetched.data["items"][0]
    assert item["category"] == EmailCategory.INTERVIEW.value
    assert item["urgency"] == EmailUrgency.URGENT.value
    assert item["deadline_note"] is not None
    assert "2026-12-01" in item["deadline_note"]


def test_draft_does_not_send_and_send_needs_confirm(db_session) -> None:
    reset_fake_mailbox()
    seed_inbox([sample_message()])
    gate = _gate(db_session)
    fetched = gate.invoke("email.fetch", {}, agent="email")
    email_id = fetched.data["items"][0]["id"]

    drafted = gate.invoke("email.draft", {"id": email_id}, agent="email")
    assert drafted.status == "ok"
    assert "not sent" in drafted.message.lower() or "Draft saved" in drafted.message
    assert sent_messages() == []

    waiting = gate.invoke("email.send", {"id": email_id}, agent="email")
    assert waiting.status == "awaiting_confirmation"
    assert sent_messages() == []

    denied = gate.resolve(waiting.pending_id, approve=False)
    assert denied.status == "denied"
    assert sent_messages() == []

    waiting = gate.invoke("email.send", {"id": email_id}, agent="email")
    sent = gate.resolve(waiting.pending_id, approve=True)
    assert sent.status == "ok"
    assert sent_messages()
    assert "hr@example.test" in sent_messages()[-1]["to"]


def test_search_finds_subject(db_session) -> None:
    reset_fake_mailbox()
    seed_inbox([sample_message(subject="Your order has shipped", body="tracking 1")])
    gate = _gate(db_session)
    gate.invoke("email.fetch", {}, agent="email")
    found = gate.invoke("email.search", {"query": "shipped"}, agent="email")
    assert found.status == "ok"
    assert found.data["items"]
