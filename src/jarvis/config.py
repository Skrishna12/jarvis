"""Load settings from environment variables and an optional .env file.

LLM keys stay optional. The default provider is `fake` so the CLI works
without a vendor account. Set JARVIS_LLM_PROVIDER=openai_compatible when
you are ready to call a real API.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Repo root: src/jarvis/config.py → parents[2] is the project root.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
_ENV_PATH = PROJECT_ROOT / ".env"
_DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "jarvis.db"
_DEFAULT_PROVIDER = "fake"
_DEFAULT_TIMEOUT = 60.0


@dataclass(frozen=True)
class Settings:
    """Typed snapshot of env-based config.

    Frozen so callers cannot accidentally mutate settings at runtime.
    """

    llm_provider: str
    llm_api_key: str
    llm_base_url: str
    llm_model: str
    llm_timeout_seconds: float
    database_path: Path
    env_file_loaded: bool


def _resolve_database_path(raw: str) -> Path:
    if not raw:
        return _DEFAULT_DB_PATH
    path = Path(raw).expanduser()
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def _parse_timeout(raw: str) -> float:
    if not raw:
        return _DEFAULT_TIMEOUT
    try:
        value = float(raw)
    except ValueError:
        return _DEFAULT_TIMEOUT
    if value <= 0:
        return _DEFAULT_TIMEOUT
    return value


def load_settings(*, env_file: Path | None = _ENV_PATH) -> Settings:
    """Read environment (and .env if present) into a Settings object.

    `env_file=None` skips the file and uses only process environment — useful
    in tests so a developer's real .env cannot leak into assertions.
    """

    loaded = False
    if env_file is not None and env_file.is_file():
        load_dotenv(env_file, override=False)
        loaded = True

    provider = os.getenv("JARVIS_LLM_PROVIDER", _DEFAULT_PROVIDER).strip().lower()
    if not provider:
        provider = _DEFAULT_PROVIDER

    return Settings(
        llm_provider=provider,
        llm_api_key=os.getenv("JARVIS_LLM_API_KEY", "").strip(),
        llm_base_url=os.getenv(
            "JARVIS_LLM_BASE_URL", "https://api.openai.com/v1"
        ).strip(),
        llm_model=os.getenv("JARVIS_LLM_MODEL", "gpt-4o-mini").strip(),
        llm_timeout_seconds=_parse_timeout(
            os.getenv("JARVIS_LLM_TIMEOUT_SECONDS", "").strip()
        ),
        database_path=_resolve_database_path(
            os.getenv("JARVIS_DATABASE_PATH", "").strip()
        ),
        env_file_loaded=loaded,
    )
