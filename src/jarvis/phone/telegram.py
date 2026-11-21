"""Telegram long-poll so the same orchestrator can be used from a phone.

The laptop/cloud process must keep running. Jarvis is not a separate mobile app.
"""

from __future__ import annotations

import time
from typing import Any

import httpx

from jarvis.agents.orchestrator import Orchestrator
from jarvis.alerts.watch import collect_alerts, deliver_alerts
from jarvis.config import Settings
from jarvis.llm.factory import build_provider
from jarvis.memory.errors import ValidationError
from jarvis.memory.store import MemoryStore
from jarvis.runtime import app_session

_API = "https://api.telegram.org"
_MAX = 3900


def telegram_url(token: str, method: str) -> str:
    return f"{_API}/bot{token}/{method}"


class TelegramClient:
    def __init__(self, token: str, *, client: httpx.Client | None = None) -> None:
        if not token:
            raise ValidationError(
                "JARVIS_TELEGRAM_BOT_TOKEN is empty. Create a bot with @BotFather, "
                "put the token in .env (never in chat), then run `jarvis phone`."
            )
        self._token = token
        self._client = client

    def get_updates(self, offset: int | None, timeout: int = 25) -> list[dict[str, Any]]:
        payload: dict[str, Any] = {"timeout": timeout}
        if offset is not None:
            payload["offset"] = offset
        data = self._post("getUpdates", payload)
        result = data.get("result")
        return result if isinstance(result, list) else []

    def send_message(self, chat_id: int | str, text: str) -> None:
        for chunk in _chunks(text):
            self._post("sendMessage", {"chat_id": chat_id, "text": chunk})

    def _post(self, method: str, payload: dict[str, Any]) -> dict[str, Any]:
        own = self._client is None
        http = self._client or httpx.Client(timeout=60.0)
        try:
            try:
                response = http.post(telegram_url(self._token, method), json=payload)
            except httpx.RequestError as exc:
                raise ValidationError(
                    f"Could not reach Telegram: {exc}. The bot token is never printed."
                ) from exc
            if response.status_code in {401, 403}:
                raise ValidationError(
                    f"Telegram rejected the bot token (HTTP {response.status_code}). "
                    "The token is never printed."
                )
            if response.status_code >= 400:
                raise ValidationError(f"Telegram request failed (HTTP {response.status_code}).")
            body = response.json()
            if not isinstance(body, dict):
                raise ValidationError("Telegram returned an unexpected payload.")
            return body
        finally:
            if own:
                http.close()


def handle_update(
    orch: Orchestrator,
    update: dict[str, Any],
    *,
    allow_chat_id: str,
    session=None,
) -> tuple[int | None, str | None]:
    message = update.get("message") or update.get("edited_message") or {}
    if not isinstance(message, dict):
        return None, None
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    text = message.get("text")
    if chat_id is None or not isinstance(text, str) or not text.strip():
        return None, None
    if allow_chat_id and str(chat_id) != allow_chat_id:
        return int(chat_id), "This Jarvis bot is locked to another Telegram account."
    if session is not None:
        MemoryStore(session).upsert("PREFERENCES", "telegram_chat_id", str(chat_id))
    result = orch.handle(text.strip())
    return int(chat_id), result.reply


def run_forever(settings: Settings) -> None:
    client = None
    if settings.telegram_bot_token:
        client = TelegramClient(settings.telegram_bot_token)
        print("Jarvis phone (Telegram). Leave this running. Ctrl+C to stop.")
        print("Message the bot anytime. Confirmations: yes / no.")
    else:
        print("Jarvis watch (no Telegram token). I will still check reminders.")
        print("Add JARVIS_TELEGRAM_BOT_TOKEN in .env to chat from your phone.")
    if settings.voice_backend == "fake":
        print("Voice calls are fake until JARVIS_VOICE_BACKEND=twilio and a number are set.")
    offset: int | None = None
    while True:
        if client is not None:
            updates = client.get_updates(offset, timeout=20)
            for update in updates:
                update_id = update.get("update_id")
                if isinstance(update_id, int):
                    offset = update_id + 1
                with app_session() as (session, live):
                    orch = Orchestrator(session, build_provider(live))
                    chat_id, reply = handle_update(
                        orch,
                        update,
                        allow_chat_id=live.telegram_chat_id,
                        session=session,
                    )
                if chat_id is not None and reply:
                    client.send_message(chat_id, reply)
        with app_session() as (session, live):
            alerts = collect_alerts(session, live)
            if alerts:
                deliver_alerts(session, alerts, settings=live, telegram=client)
                for alert in alerts:
                    print(alert.title + ":", alert.body[:200])
        if client is None:
            time.sleep(20)


def _chunks(text: str) -> list[str]:
    if len(text) <= _MAX:
        return [text or "(empty reply)"]
    parts: list[str] = []
    rest = text
    while rest:
        parts.append(rest[:_MAX])
        rest = rest[_MAX:]
    return parts
