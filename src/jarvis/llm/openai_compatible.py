"""OpenAI-compatible Chat Completions client (OpenAI, Groq, many local servers).

Talks HTTP JSON. We do not import an official vendor SDK so swapping hosts
is a URL + key change, not a rewrite.
"""

from __future__ import annotations

import json
from collections.abc import Iterator, Sequence
from typing import Any

import httpx

from jarvis.llm.base import LLMProvider
from jarvis.llm.errors import LlmConfigError, LlmProviderError, LlmResponseError
from jarvis.llm.prompts import (
    classify_prompt,
    parse_label,
    validate_labels,
    validate_messages,
)
from jarvis.llm.types import ChatMessage, ClassifyResult, GenerateResult

_PROVIDER = "openai_compatible"


class OpenAICompatibleProvider(LLMProvider):
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float = 60.0,
        client: httpx.Client | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._timeout = timeout_seconds
        self._client = client

    def generate(
        self,
        messages: Sequence[ChatMessage],
        *,
        temperature: float = 0.2,
    ) -> GenerateResult:
        body = self._post_json(
            {
                "model": self._model,
                "messages": _as_dicts(validate_messages(messages)),
                "temperature": temperature,
                "stream": False,
            }
        )
        text = _content_from_completion(body)
        return GenerateResult(text=text, model=self._model, provider=_PROVIDER)

    def stream(
        self,
        messages: Sequence[ChatMessage],
        *,
        temperature: float = 0.2,
    ) -> Iterator[str]:
        payload = {
            "model": self._model,
            "messages": _as_dicts(validate_messages(messages)),
            "temperature": temperature,
            "stream": True,
        }
        client = self._owned_client()
        close = self._client is None
        try:
            try:
                with client.stream(
                    "POST",
                    self._url("/chat/completions"),
                    json=payload,
                    headers=self._headers(),
                ) as response:
                    self._raise_for_status(response)
                    yielded = False
                    for line in response.iter_lines():
                        chunk = _delta_from_sse_line(line)
                        if chunk:
                            yielded = True
                            yield chunk
                    if not yielded:
                        raise LlmResponseError(
                            "The model stream ended without any text. "
                            "Check the model name and try generate() instead."
                        )
            except httpx.TimeoutException as exc:
                raise LlmProviderError(
                    f"The LLM request timed out after {self._timeout}s. "
                    "Increase JARVIS_LLM_TIMEOUT_SECONDS or retry."
                ) from exc
            except httpx.RequestError as exc:
                raise LlmProviderError(
                    f"Could not reach the LLM at {self._base_url}: {exc}. "
                    "Check JARVIS_LLM_BASE_URL and your network."
                ) from exc
        finally:
            if close:
                client.close()

    def classify(
        self,
        text: str,
        labels: Sequence[str],
        *,
        instruction: str | None = None,
    ) -> ClassifyResult:
        if not text.strip():
            raise LlmConfigError("Classification text cannot be empty.")
        cleaned = validate_labels(labels)
        result = self.generate(
            classify_prompt(text, cleaned, instruction),
            temperature=0.0,
        )
        label = parse_label(result.text, cleaned)
        return ClassifyResult(
            label=label,
            model=self._model,
            provider=_PROVIDER,
            raw_text=result.text,
        )

    def _post_json(self, payload: dict[str, Any]) -> dict[str, Any]:
        client = self._owned_client()
        close = self._client is None
        try:
            try:
                response = client.post(
                    self._url("/chat/completions"),
                    json=payload,
                    headers=self._headers(),
                )
            except httpx.TimeoutException as exc:
                raise LlmProviderError(
                    f"The LLM request timed out after {self._timeout}s. "
                    "Increase JARVIS_LLM_TIMEOUT_SECONDS or retry."
                ) from exc
            except httpx.RequestError as exc:
                raise LlmProviderError(
                    f"Could not reach the LLM at {self._base_url}: {exc}. "
                    "Check JARVIS_LLM_BASE_URL and your network."
                ) from exc
            self._raise_for_status(response)
            try:
                body = response.json()
            except json.JSONDecodeError as exc:
                raise LlmResponseError(
                    "The LLM returned a non-JSON body. Check JARVIS_LLM_BASE_URL."
                ) from exc
            if not isinstance(body, dict):
                raise LlmResponseError("The LLM JSON was not an object.")
            return body
        finally:
            if close:
                client.close()

    def _owned_client(self) -> httpx.Client:
        if self._client is not None:
            return self._client
        return httpx.Client(timeout=self._timeout)

    def _url(self, path: str) -> str:
        return f"{self._base_url}{path}"

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.is_success:
            return
        status = response.status_code
        # Never echo response bodies that might contain redirected secrets.
        if status in {401, 403}:
            raise LlmProviderError(
                f"The LLM rejected the request (HTTP {status}). "
                "Check JARVIS_LLM_API_KEY and that the key is allowed for this host. "
                "The key is never printed."
            )
        if status == 429:
            raise LlmProviderError(
                "The LLM rate-limited the request (HTTP 429). Wait and retry."
            )
        if status == 404:
            raise LlmProviderError(
                "The LLM endpoint was not found (HTTP 404). "
                "Check JARVIS_LLM_BASE_URL (it should usually end in /v1)."
            )
        raise LlmProviderError(
            f"The LLM request failed (HTTP {status}). "
            "Check the model name, base URL, and provider status page."
        )


def _as_dicts(messages: Sequence[ChatMessage]) -> list[dict[str, str]]:
    return [{"role": m.role, "content": m.content} for m in messages]


def _content_from_completion(body: dict[str, Any]) -> str:
    choices = body.get("choices")
    if not isinstance(choices, list) or not choices:
        raise LlmResponseError(
            "The LLM response had no choices. The model name may be wrong."
        )
    first = choices[0]
    if not isinstance(first, dict):
        raise LlmResponseError("The LLM choice was not an object.")
    message = first.get("message")
    if not isinstance(message, dict):
        raise LlmResponseError("The LLM choice had no message object.")
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise LlmResponseError(
            "The LLM returned an empty message. Try a different model or prompt."
        )
    return content


def _delta_from_sse_line(line: str) -> str:
    stripped = line.strip()
    if not stripped or stripped.startswith(":"):
        return ""
    if not stripped.startswith("data:"):
        return ""
    data = stripped[5:].strip()
    if data == "[DONE]":
        return ""
    try:
        payload = json.loads(data)
    except json.JSONDecodeError as exc:
        raise LlmResponseError(
            "The LLM stream sent a line that was not JSON. "
            "Check JARVIS_LLM_BASE_URL points at a Chat Completions API."
        ) from exc
    if not isinstance(payload, dict):
        return ""
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    first = choices[0]
    if not isinstance(first, dict):
        return ""
    delta = first.get("delta")
    if not isinstance(delta, dict):
        return ""
    content = delta.get("content")
    if isinstance(content, str):
        return content
    return ""
