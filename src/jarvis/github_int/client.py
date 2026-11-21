"""Read-only GitHub access. Never push, merge, or comment."""

from __future__ import annotations

from typing import Any

import httpx

from jarvis.config import Settings, load_settings
from jarvis.memory.errors import ValidationError

_FAKE_REPOS = [
    {
        "full_name": "local/jarvis",
        "description": "Personal assistant (fake GitHub data)",
        "html_url": "https://github.com/local/jarvis",
    }
]
_FAKE_ISSUES = [
    {"number": 1, "title": "Wire calendar", "state": "open", "html_url": "https://example.test/1"}
]
_FAKE_PULLS = [
    {"number": 8, "title": "Email agent", "state": "open", "html_url": "https://example.test/8"}
]


class GitHubClient:
    def __init__(self, *, backend: str, token: str) -> None:
        self._backend = backend
        self._token = token

    def repos(self, limit: int = 10) -> list[dict[str, Any]]:
        if self._backend == "fake":
            return _FAKE_REPOS[:limit]
        return self._get("/user/repos", params={"per_page": min(limit, 30), "sort": "updated"})

    def issues(self, repo: str, limit: int = 10) -> list[dict[str, Any]]:
        repo = _repo(repo)
        if self._backend == "fake":
            return _FAKE_ISSUES[:limit]
        return self._get(f"/repos/{repo}/issues", params={"state": "open", "per_page": min(limit, 30)})

    def pulls(self, repo: str, limit: int = 10) -> list[dict[str, Any]]:
        repo = _repo(repo)
        if self._backend == "fake":
            return _FAKE_PULLS[:limit]
        return self._get(f"/repos/{repo}/pulls", params={"state": "open", "per_page": min(limit, 30)})

    def _get(self, path: str, params: dict | None = None) -> list[dict[str, Any]]:
        if not self._token:
            raise ValidationError(
                "JARVIS_GITHUB_TOKEN is empty. Put a read-only token in .env "
                "(never paste it in chat) or keep JARVIS_GITHUB_BACKEND=fake."
            )
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "jarvis-cli",
        }
        try:
            response = httpx.get(
                f"https://api.github.com{path}",
                headers=headers,
                params=params or {},
                timeout=30.0,
            )
        except httpx.RequestError as exc:
            raise ValidationError(f"Could not reach GitHub: {exc}.") from exc
        if response.status_code in {401, 403}:
            raise ValidationError(
                f"GitHub rejected the token (HTTP {response.status_code}). "
                "The token is never printed."
            )
        if response.status_code >= 400:
            raise ValidationError(f"GitHub request failed (HTTP {response.status_code}).")
        body = response.json()
        if not isinstance(body, list):
            raise ValidationError("GitHub returned an unexpected payload.")
        return body


def build_github_client(settings: Settings | None = None) -> GitHubClient:
    cfg = settings or load_settings()
    backend = cfg.github_backend
    if backend not in {"fake", "api"}:
        raise ValidationError(
            f"Unknown JARVIS_GITHUB_BACKEND={backend!r}. Use fake or api."
        )
    return GitHubClient(backend=backend, token=cfg.github_token)


def _repo(raw: str) -> str:
    text = raw.strip()
    if "/" not in text:
        raise ValidationError("Repo must look like owner/name.")
    return text
