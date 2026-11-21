from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from jarvis.core.clock import utc_now
from jarvis.db.models import Document, DocumentChunk
from jarvis.memory.errors import ValidationError

_CHUNK = 800
_MAX_FILE = 400_000
_TEXT_SUFFIXES = {".md", ".txt", ".py", ".rst", ".json", ".toml", ".yml", ".yaml"}


@dataclass(frozen=True)
class SearchHit:
    document_id: str
    path: str
    title: str
    snippet: str
    score: int


class DocumentStore:
    def __init__(self, session: Session) -> None:
        self._session = session

    def ingest(self, raw_path: str) -> tuple[str, int]:
        path = Path(raw_path).expanduser()
        if not path.is_file():
            raise ValidationError(
                f"File not found: {path}. Give an existing local text file path."
            )
        if path.suffix.lower() not in _TEXT_SUFFIXES and path.suffix.lower() not in {""}:
            raise ValidationError(
                f"Refusing to ingest {path.suffix} files. Use markdown/text/code."
            )
        data = path.read_bytes()
        if len(data) > _MAX_FILE:
            raise ValidationError("File is larger than 400KB; split it first.")
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValidationError("File is not valid UTF-8 text.") from exc
        chunks = _chunk_text(text)
        if not chunks:
            raise ValidationError("File was empty.")
        existing = self._session.scalar(select(Document).where(Document.path == str(path.resolve())))
        now = utc_now()
        if existing is None:
            doc = Document(
                id=str(uuid4()),
                path=str(path.resolve()),
                title=path.name,
                created_at=now,
                updated_at=now,
            )
            self._session.add(doc)
        else:
            doc = existing
            doc.updated_at = now
            for old in self._session.scalars(
                select(DocumentChunk).where(DocumentChunk.document_id == doc.id)
            ).all():
                self._session.delete(old)
        self._session.flush()
        for i, chunk in enumerate(chunks):
            self._session.add(
                DocumentChunk(
                    id=str(uuid4()),
                    document_id=doc.id,
                    ordinal=i,
                    text=chunk,
                )
            )
        self._session.flush()
        return doc.id, len(chunks)

    def search(self, query: str, *, limit: int = 5) -> list[SearchHit]:
        words = [w.lower() for w in query.split() if len(w) > 1]
        if not words:
            raise ValidationError("Search query cannot be empty.")
        chunks = self._session.scalars(select(DocumentChunk)).all()
        scored: list[tuple[int, DocumentChunk]] = []
        for chunk in chunks:
            hay = chunk.text.lower()
            score = sum(hay.count(word) for word in words)
            if score:
                scored.append((score, chunk))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        hits: list[SearchHit] = []
        for score, chunk in scored[:limit]:
            doc = self._session.get(Document, chunk.document_id)
            if doc is None:
                continue
            snippet = chunk.text.strip().replace("\n", " ")[:240]
            hits.append(
                SearchHit(
                    document_id=doc.id,
                    path=doc.path,
                    title=doc.title,
                    snippet=snippet,
                    score=score,
                )
            )
        return hits


def _chunk_text(text: str) -> list[str]:
    parts: list[str] = []
    buf: list[str] = []
    size = 0
    for para in text.split("\n\n"):
        para = para.strip()
        if not para:
            continue
        if size + len(para) > _CHUNK and buf:
            parts.append("\n\n".join(buf))
            buf = [para]
            size = len(para)
        else:
            buf.append(para)
            size += len(para)
    if buf:
        parts.append("\n\n".join(buf))
    return parts
