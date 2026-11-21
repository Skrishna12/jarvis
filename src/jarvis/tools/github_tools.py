from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from jarvis.github_int.client import build_github_client
from jarvis.security.levels import PermissionLevel
from jarvis.tools.base import Tool, ToolResult


class GitHubReposTool(Tool):
    name = "github.repos"
    description = "List repositories (read-only)."
    agent = "github"
    level = PermissionLevel.READ

    def run(self, session: Session, payload: dict[str, Any]) -> ToolResult:
        del session
        items = build_github_client().repos(int(payload.get("limit") or 10))
        if not items:
            return ToolResult(True, "No repositories.", {"items": []})
        lines = [str(item.get("full_name") or item.get("name")) for item in items]
        return ToolResult(True, "\n".join(lines), {"items": items})


class GitHubIssuesTool(Tool):
    name = "github.issues"
    description = "List open issues for owner/name (read-only)."
    agent = "github"
    level = PermissionLevel.READ

    def run(self, session: Session, payload: dict[str, Any]) -> ToolResult:
        del session
        repo = str(payload.get("repo") or "")
        items = build_github_client().issues(repo, int(payload.get("limit") or 10))
        if not items:
            return ToolResult(True, f"No open issues in {repo}.", {"items": []})
        lines = [f"#{item.get('number')} {item.get('title')}" for item in items]
        return ToolResult(True, "\n".join(lines), {"items": items})


class GitHubPullsTool(Tool):
    name = "github.pulls"
    description = "List open pull requests for owner/name (read-only)."
    agent = "github"
    level = PermissionLevel.READ

    def run(self, session: Session, payload: dict[str, Any]) -> ToolResult:
        del session
        repo = str(payload.get("repo") or "")
        items = build_github_client().pulls(repo, int(payload.get("limit") or 10))
        if not items:
            return ToolResult(True, f"No open pull requests in {repo}.", {"items": []})
        lines = [f"#{item.get('number')} {item.get('title')}" for item in items]
        return ToolResult(True, "\n".join(lines), {"items": items})
