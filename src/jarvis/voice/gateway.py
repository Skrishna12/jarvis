"""Speak an update: fake (log only) or Twilio outbound call with <Say>."""

from __future__ import annotations

from dataclasses import dataclass
from xml.sax.saxutils import escape

import httpx

from jarvis.config import Settings, load_settings
from jarvis.memory.errors import ValidationError

_FAKE_CALLS: list[str] = []
_SAY_LIMIT = 480


def fake_calls() -> list[str]:
    return list(_FAKE_CALLS)


def reset_fake_calls() -> None:
    _FAKE_CALLS.clear()


@dataclass(frozen=True)
class CallResult:
    backend: str
    spoken: str
    placed: bool


class VoiceGateway:
    def __init__(self, settings: Settings | None = None, *, client: httpx.Client | None = None) -> None:
        self._settings = settings or load_settings()
        self._client = client

    def speak(self, text: str, *, call: bool = True) -> CallResult:
        spoken = " ".join(text.split())
        if len(spoken) > _SAY_LIMIT:
            spoken = spoken[:_SAY_LIMIT].rstrip() + "."
        if not spoken:
            raise ValidationError("Nothing to say on the call.")
        backend = self._settings.voice_backend
        if backend == "fake" or not call:
            _FAKE_CALLS.append(spoken)
            return CallResult(backend="fake", spoken=spoken, placed=False)
        if backend == "twilio":
            self._twilio_call(spoken)
            return CallResult(backend="twilio", spoken=spoken, placed=True)
        raise ValidationError(
            f"Unknown JARVIS_VOICE_BACKEND={backend!r}. Use fake or twilio."
        )

    def _twilio_call(self, spoken: str) -> None:
        cfg = self._settings
        if not cfg.twilio_account_sid or not cfg.twilio_auth_token:
            raise ValidationError(
                "Twilio SID/token missing. Put them in .env (never in chat) "
                "or keep JARVIS_VOICE_BACKEND=fake."
            )
        if not cfg.twilio_from or not cfg.voice_to:
            raise ValidationError(
                "Set JARVIS_TWILIO_FROM and JARVIS_VOICE_TO (E.164, e.g. +91…) in .env."
            )
        twiml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<Response><Say voice=\"Polly.Aditi\">"
            f"{escape(spoken)}"
            "</Say></Response>"
        )
        url = (
            "https://api.twilio.com/2010-04-01/Accounts/"
            f"{cfg.twilio_account_sid}/Calls.json"
        )
        own = self._client is None
        http = self._client or httpx.Client(timeout=30.0)
        try:
            try:
                response = http.post(
                    url,
                    data={
                        "To": cfg.voice_to,
                        "From": cfg.twilio_from,
                        "Twiml": twiml,
                    },
                    auth=(cfg.twilio_account_sid, cfg.twilio_auth_token),
                )
            except httpx.RequestError as exc:
                raise ValidationError(f"Could not reach Twilio: {exc}.") from exc
            if response.status_code in {401, 403}:
                raise ValidationError(
                    f"Twilio rejected the credentials (HTTP {response.status_code}). "
                    "Secrets are never printed."
                )
            if response.status_code >= 400:
                raise ValidationError(f"Twilio call failed (HTTP {response.status_code}).")
        finally:
            if own:
                http.close()
