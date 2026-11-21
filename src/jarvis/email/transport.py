"""Mailbox interface: fetch mail in, send mail out.

Default backend is `fake` so tests and first-run never touch a real inbox.
Set JARVIS_EMAIL_BACKEND=imap and fill IMAP/SMTP settings to use a real host.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from jarvis.config import Settings, load_settings
from jarvis.email.errors import EmailConfigError


@dataclass(frozen=True)
class IncomingMessage:
    internet_id: str
    from_addr: str
    to_addr: str
    subject: str
    body: str
    received_at: datetime


class MailTransport(Protocol):
    def fetch_recent(self, limit: int) -> list[IncomingMessage]:
        """Newest first, up to `limit` messages."""

    def send(self, *, to: str, subject: str, body: str) -> None:
        """Deliver a message. Callers must already have level-2 confirmation."""


def build_transport(settings: Settings | None = None) -> MailTransport:
    cfg = settings or load_settings()
    backend = cfg.email_backend
    if backend == "fake":
        from jarvis.email.fake import get_fake_mailbox

        return get_fake_mailbox()
    if backend == "imap":
        from jarvis.email.imap_smtp import ImapSmtpTransport

        if not cfg.email_address:
            raise EmailConfigError(
                "JARVIS_EMAIL_ADDRESS is empty. Set it in .env "
                "(and JARVIS_EMAIL_PASSWORD — an app password, not your login password)."
            )
        if not cfg.email_password:
            raise EmailConfigError(
                "JARVIS_EMAIL_PASSWORD is empty. For Gmail, create an app password "
                "and put it in .env. Do not paste it into chat."
            )
        return ImapSmtpTransport(cfg)
    raise EmailConfigError(
        f"Unknown JARVIS_EMAIL_BACKEND={backend!r}. Use fake or imap."
    )
