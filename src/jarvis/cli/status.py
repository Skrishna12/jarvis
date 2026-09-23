"""Print a short status snapshot (no secrets)."""

from __future__ import annotations

from jarvis import __version__
from jarvis.config import load_settings
from jarvis.db.migrate import current_revision


def print_status() -> None:
    settings = load_settings()
    key_state = "set" if settings.llm_api_key else "not set"
    env_state = "yes" if settings.env_file_loaded else "no"
    db_path = settings.database_path
    if db_path.is_file():
        revision = current_revision(db_path) or "unknown (file exists, no Alembic revision)"
        db_state = f"exists, revision {revision}"
    else:
        db_state = "missing — run: jarvis db upgrade"

    print(f"Jarvis {__version__} — Milestone 3 (LLM providers).")
    print("Agents and the chat loop are not wired yet.")
    print(f"  .env file loaded: {env_state}")
    print(f"  JARVIS_LLM_PROVIDER: {settings.llm_provider}")
    print(f"  JARVIS_LLM_API_KEY: {key_state}")
    print(f"  JARVIS_LLM_MODEL: {settings.llm_model}")
    print(f"  JARVIS_LLM_BASE_URL: {settings.llm_base_url}")
    print(f"  database: {db_path} ({db_state})")
