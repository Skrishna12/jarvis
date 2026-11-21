from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from jarvis.docs.store import DocumentStore
from jarvis.security.levels import PermissionLevel
from jarvis.tools.base import Tool, ToolResult
from jarvis.tools.serialize import record_data


class DocsIngestTool(Tool):
    name = "docs.ingest"
    description = "Index a local text/markdown file for search."
    agent = "docs"
    level = PermissionLevel.SAFE

    def run(self, session: Session, payload: dict[str, Any]) -> ToolResult:
        doc_id, chunks = DocumentStore(session).ingest(str(payload.get("path", "")))
        return ToolResult(
            True,
            f"Indexed {chunks} chunk(s) from that file ({doc_id[:8]}).",
            {"document_id": doc_id, "chunks": chunks},
        )


class DocsSearchTool(Tool):
    name = "docs.search"
    description = "Keyword search over ingested local documents."
    agent = "docs"
    level = PermissionLevel.READ

    def run(self, session: Session, payload: dict[str, Any]) -> ToolResult:
        hits = DocumentStore(session).search(
            str(payload.get("query", "")),
            limit=int(payload.get("limit") or 5),
        )
        if not hits:
            return ToolResult(True, "No matching document chunks.", {"items": []})
        lines = [f"{h.score} {h.title}: {h.snippet}" for h in hits]
        return ToolResult(True, "\n".join(lines), {"items": [record_data(h) for h in hits]})
