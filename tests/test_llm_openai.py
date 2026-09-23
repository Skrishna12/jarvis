"""OpenAI-compatible provider with a mocked HTTP client (no real API)."""

from __future__ import annotations

import httpx
import pytest

from jarvis.llm.errors import LlmProviderError, LlmResponseError
from jarvis.llm.openai_compatible import OpenAICompatibleProvider
from jarvis.llm.types import ChatMessage

_SECRET = "sk-test-not-a-real-key"


def _provider(handler) -> OpenAICompatibleProvider:
    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport, timeout=5.0)
    return OpenAICompatibleProvider(
        base_url="https://example.test/v1",
        api_key=_SECRET,
        model="test-model",
        client=client,
    )


def test_generate_reads_message_content() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/chat/completions")
        assert request.headers["Authorization"] == f"Bearer {_SECRET}"
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "  hello from mock  "}}]},
        )

    result = _provider(handler).generate([ChatMessage(role="user", content="hi")])
    assert result.text == "  hello from mock  "
    assert result.provider == "openai_compatible"


def test_stream_yields_delta_chunks() -> None:
    sse = (
        'data: {"choices":[{"delta":{"content":"Hel"}}]}\n\n'
        'data: {"choices":[{"delta":{"content":"lo"}}]}\n\n'
        "data: [DONE]\n\n"
    )

    def handler(request: httpx.Request) -> httpx.Response:
        assert b'"stream": true' in request.content
        return httpx.Response(
            200,
            content=sse.encode("utf-8"),
            headers={"Content-Type": "text/event-stream"},
        )

    text = "".join(
        _provider(handler).stream([ChatMessage(role="user", content="hi")])
    )
    assert text == "Hello"


def test_classify_parses_label_from_model_text() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "TASK\n"}}]},
        )

    result = _provider(handler).classify("add milk", ["CHAT", "TASK"])
    assert result.label == "TASK"


def test_http_401_does_not_include_api_key() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": {"message": "bad key"}})

    with pytest.raises(LlmProviderError, match="HTTP 401") as info:
        _provider(handler).generate([ChatMessage(role="user", content="hi")])
    assert _SECRET not in str(info.value)


def test_empty_completion_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": [{"message": {"content": "   "}}]})

    with pytest.raises(LlmResponseError, match="empty message"):
        _provider(handler).generate([ChatMessage(role="user", content="hi")])
