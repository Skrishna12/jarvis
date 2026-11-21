"""In-memory mailbox for tests and for running without IMAP credentials."""

from __future__ import annotations

from jarvis.core.clock import utc_now
from jarvis.email.transport import IncomingMessage

_inbox: list[IncomingMessage] = []
_sent: list[dict[str, str]] = []


class FakeMailbox:
    def fetch_recent(self, limit: int) -> list[IncomingMessage]:
        return list(reversed(_inbox[-limit:])) if limit else []

    def send(self, *, to: str, subject: str, body: str) -> None:
        _sent.append({"to": to, "subject": subject, "body": body})


def get_fake_mailbox() -> FakeMailbox:
    return FakeMailbox()


def seed_inbox(messages: list[IncomingMessage]) -> None:
    _inbox.clear()
    _inbox.extend(messages)


def sent_messages() -> list[dict[str, str]]:
    return list(_sent)


def reset_fake_mailbox() -> None:
    _inbox.clear()
    _sent.clear()


def sample_message(
    *,
    internet_id: str = "<hr@example.test>",
    from_addr: str = "hr@example.test",
    to_addr: str = "me@example.test",
    subject: str = "Interview next week",
    body: str = "Can you interview on 2026-12-01T10:00:00?",
) -> IncomingMessage:
    return IncomingMessage(
        internet_id=internet_id,
        from_addr=from_addr,
        to_addr=to_addr,
        subject=subject,
        body=body,
        received_at=utc_now(),
    )
