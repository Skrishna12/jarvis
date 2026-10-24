"""Pick an LLMProvider from Settings."""

from __future__ import annotations

from jarvis.config import Settings
from jarvis.llm.base import LLMProvider
from jarvis.llm.errors import LlmConfigError
from jarvis.llm.fake import FakeProvider
from jarvis.llm.openai_compatible import OpenAICompatibleProvider

_KNOWN = ("fake", "openai_compatible")


def build_provider(settings: Settings) -> LLMProvider:
    name = settings.llm_provider
    if name == "fake":
        return FakeProvider(model=settings.llm_model or "fake-model")
    if name == "openai_compatible":
        if not settings.llm_base_url:
            raise LlmConfigError(
                "JARVIS_LLM_BASE_URL is empty. "
                "Set it to an OpenAI-compatible root such as https://api.openai.com/v1."
            )
        if not settings.llm_model:
            raise LlmConfigError(
                "JARVIS_LLM_MODEL is empty. Set a model name the host accepts."
            )
        return OpenAICompatibleProvider(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            timeout_seconds=settings.llm_timeout_seconds,
        )
    known = ", ".join(_KNOWN)
    raise LlmConfigError(
        f"Unknown JARVIS_LLM_PROVIDER={name!r}. Use one of: {known}."
    )
