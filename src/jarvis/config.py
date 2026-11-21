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
_DEFAULT_SUMMARY_EVERY = 10
_DEFAULT_NEWS_NATIONAL = (
    "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en"
)
_DEFAULT_NEWS_WORLD = (
    "https://news.google.com/rss/headlines/section/topic/WORLD"
    "?hl=en-IN&gl=IN&ceid=IN:en"
)
_DEFAULT_NEWS_PER_SECTION = 6


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
    summary_every_messages: int
    email_backend: str
    email_address: str
    email_password: str
    email_imap_host: str
    email_imap_port: int
    email_smtp_host: str
    email_smtp_port: int
    github_backend: str
    github_token: str
    news_national_feed: str
    news_world_feed: str
    news_per_section: int
    database_path: Path
    env_file_loaded: bool


def _resolve_database_path(raw: str) -> Path:
    if not raw:
        return _DEFAULT_DB_PATH
    path = Path(raw).expanduser()
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def _parse_positive_int(raw: str, default: int) -> int:
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    if value < 2:
        return default
    return value


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
        summary_every_messages=_parse_positive_int(
            os.getenv("JARVIS_SUMMARY_EVERY", "").strip(),
            _DEFAULT_SUMMARY_EVERY,
        ),
        email_backend=(os.getenv("JARVIS_EMAIL_BACKEND", "fake").strip().lower() or "fake"),
        email_address=os.getenv("JARVIS_EMAIL_ADDRESS", "").strip(),
        email_password=os.getenv("JARVIS_EMAIL_PASSWORD", "").strip(),
        email_imap_host=os.getenv("JARVIS_EMAIL_IMAP_HOST", "imap.gmail.com").strip(),
        email_imap_port=_parse_positive_int(
            os.getenv("JARVIS_EMAIL_IMAP_PORT", "").strip(), 993
        ),
        email_smtp_host=os.getenv("JARVIS_EMAIL_SMTP_HOST", "smtp.gmail.com").strip(),
        email_smtp_port=_parse_positive_int(
            os.getenv("JARVIS_EMAIL_SMTP_PORT", "").strip(), 587
        ),
        github_backend=(
            os.getenv("JARVIS_GITHUB_BACKEND", "fake").strip().lower() or "fake"
        ),
        github_token=os.getenv("JARVIS_GITHUB_TOKEN", "").strip(),
        news_national_feed=(
            os.getenv("JARVIS_NEWS_NATIONAL_FEED", "").strip() or _DEFAULT_NEWS_NATIONAL
        ),
        news_world_feed=(
            os.getenv("JARVIS_NEWS_WORLD_FEED", "").strip() or _DEFAULT_NEWS_WORLD
        ),
        news_per_section=_parse_positive_int(
            os.getenv("JARVIS_NEWS_PER_SECTION", "").strip(),
            _DEFAULT_NEWS_PER_SECTION,
        ),
        database_path=_resolve_database_path(
            os.getenv("JARVIS_DATABASE_PATH", "").strip()
        ),
        env_file_loaded=loaded,
    )
