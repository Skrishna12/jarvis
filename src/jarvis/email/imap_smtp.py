"""Real IMAP fetch + SMTP send. Credentials come from Settings, never from code."""

from __future__ import annotations

import email as email_lib
import imaplib
import smtplib
import ssl
from email.header import decode_header, make_header
from email.message import EmailMessage
from email.utils import parsedate_to_datetime

from jarvis.config import Settings
from jarvis.core.clock import utc_now
from jarvis.email.errors import EmailConfigError, EmailError
from jarvis.email.transport import IncomingMessage


class ImapSmtpTransport:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def fetch_recent(self, limit: int) -> list[IncomingMessage]:
        limit = max(1, min(limit, 50))
        try:
            client = imaplib.IMAP4_SSL(
                self._settings.email_imap_host,
                self._settings.email_imap_port,
            )
        except OSError as exc:
            raise EmailError(
                f"Could not reach IMAP {self._settings.email_imap_host}: {exc}. "
                "Check JARVIS_EMAIL_IMAP_HOST and your network."
            ) from exc
        try:
            try:
                status, _ = client.login(
                    self._settings.email_address, self._settings.email_password
                )
            except imaplib.IMAP4.error as exc:
                raise EmailConfigError(
                    "IMAP login failed. Check JARVIS_EMAIL_ADDRESS and "
                    "JARVIS_EMAIL_PASSWORD (Gmail needs an app password). "
                    "The password is never printed."
                ) from exc
            if status != "OK":
                raise EmailConfigError("IMAP login was rejected.")
            client.select("INBOX", readonly=True)
            status, data = client.search(None, "ALL")
            if status != "OK" or not data or not data[0]:
                return []
            ids = data[0].split()[-limit:]
            messages: list[IncomingMessage] = []
            for msg_id in reversed(ids):
                status, fetched = client.fetch(msg_id, "(RFC822)")
                if status != "OK" or not fetched or not fetched[0]:
                    continue
                raw = fetched[0][1]
                if not isinstance(raw, (bytes, bytearray)):
                    continue
                messages.append(_parse_rfc822(bytes(raw)))
            return messages
        finally:
            try:
                client.logout()
            except Exception:
                pass

    def send(self, *, to: str, subject: str, body: str) -> None:
        msg = EmailMessage()
        msg["From"] = self._settings.email_address
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        context = ssl.create_default_context()
        try:
            with smtplib.SMTP(
                self._settings.email_smtp_host,
                self._settings.email_smtp_port,
                timeout=30,
            ) as smtp:
                smtp.starttls(context=context)
                smtp.login(self._settings.email_address, self._settings.email_password)
                smtp.send_message(msg)
        except smtplib.SMTPAuthenticationError as exc:
            raise EmailConfigError(
                "SMTP login failed. Check JARVIS_EMAIL_PASSWORD. "
                "The password is never printed."
            ) from exc
        except OSError as exc:
            raise EmailError(
                f"Could not send via SMTP {self._settings.email_smtp_host}: {exc}."
            ) from exc


def _parse_rfc822(raw: bytes) -> IncomingMessage:
    parsed = email_lib.message_from_bytes(raw)
    subject = _decode_header(parsed.get("Subject", "(no subject)"))
    from_addr = str(parsed.get("From", ""))
    to_addr = str(parsed.get("To", ""))
    internet_id = str(parsed.get("Message-ID") or parsed.get("Message-Id") or subject)
    received = utc_now()
    date_header = parsed.get("Date")
    if date_header:
        try:
            received = parsedate_to_datetime(date_header).replace(tzinfo=None)
        except (TypeError, ValueError, IndexError):
            pass
    return IncomingMessage(
        internet_id=internet_id[:512],
        from_addr=from_addr[:512],
        to_addr=to_addr[:512],
        subject=subject[:512],
        body=_plain_body(parsed)[:20_000],
        received_at=received,
    )


def _decode_header(value: str) -> str:
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return value


def _plain_body(message: email_lib.message.Message) -> str:
    if message.is_multipart():
        for part in message.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                if isinstance(payload, bytes):
                    charset = part.get_content_charset() or "utf-8"
                    return payload.decode(charset, errors="replace")
        return ""
    payload = message.get_payload(decode=True)
    if isinstance(payload, bytes):
        charset = message.get_content_charset() or "utf-8"
        return payload.decode(charset, errors="replace")
    if isinstance(payload, str):
        return payload
    return ""
