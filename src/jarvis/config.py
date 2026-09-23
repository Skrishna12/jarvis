"""Load settings from environment variables and an optional .env file.

Milestone 1: we only load and expose settings. We do not require an API key
yet (the LLM is Milestone 3). Missing optional values stay empty strings
instead of crashing, so you can run the CLI before you have a key.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Repo root: src/jarvis/config.py → parents[2] is the project root.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_ENV_PATH = _PROJECT_ROOT / ".env"


@dataclass(frozen=True)
class Settings:
    """Typed snapshot of env-based config.

    Frozen so callers cannot accidentally mutate settings at runtime.
    """

    llm_api_key: str
    llm_base_url: str
    llm_model: str
    env_file_loaded: bool


def load_settings(*, env_file: Path | None = _ENV_PATH) -> Settings:
    """Read environment (and .env if present) into a Settings object.

    `env_file=None` skips the file and uses only process environment — useful
    in tests so a developer's real .env cannot leak into assertions.
    """

    loaded = False
    if env_file is not None and env_file.is_file():
        load_dotenv(env_file, override=False)
        loaded = True

    return Settings(
        llm_api_key=os.getenv("JARVIS_LLM_API_KEY", "").strip(),
        llm_base_url=os.getenv(
            "JARVIS_LLM_BASE_URL", "https://api.openai.com/v1"
        ).strip(),
        llm_model=os.getenv("JARVIS_LLM_MODEL", "gpt-4o-mini").strip(),
        env_file_loaded=loaded,
    )
