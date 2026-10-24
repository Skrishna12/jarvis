"""Create / read / update / delete categorized memories."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from jarvis.db.models import Memory
from jarvis.memory.categories import MemoryCategory
from jarvis.memory.errors import MemoryNotFoundError, ValidationError

_MAX_KEY_LEN = 256
_MAX_VALUE_LEN = 16_384


@dataclass(frozen=True)
class MemoryRecord:
    id: str
    category: MemoryCategory
    key: str
    value: str
    created_at: datetime
    updated_at: datetime


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _parse_category(raw: str) -> MemoryCategory:
    try:
        return MemoryCategory(raw)
    except ValueError as exc:
        allowed = ", ".join(c.value for c in MemoryCategory)
        raise ValidationError(
            f"Unknown memory category {raw!r}. Use one of: {allowed}."
        ) from exc


def _normalize_key(key: str) -> str:
    cleaned = key.strip()
    if not cleaned:
        raise ValidationError("Memory key cannot be empty.")
    if len(cleaned) > _MAX_KEY_LEN:
        raise ValidationError(
            f"Memory key is {len(cleaned)} characters; max is {_MAX_KEY_LEN}."
        )
    return cleaned


def _normalize_value(value: str) -> str:
    if value is None:
        raise ValidationError("Memory value cannot be empty.")
    if len(value) > _MAX_VALUE_LEN:
        raise ValidationError(
            f"Memory value is {len(value)} characters; max is {_MAX_VALUE_LEN}."
        )
    return value


def _to_record(row: Memory) -> MemoryRecord:
    return MemoryRecord(
        id=row.id,
        category=MemoryCategory(row.category),
        key=row.key,
        value=row.value,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class MemoryStore:
    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert(self, category: str, key: str, value: str) -> MemoryRecord:
        """Insert a fact, or replace the value if that key already exists."""
        cat = _parse_category(category)
        key = _normalize_key(key)
        value = _normalize_value(value)
        now = _utc_now()

        existing = self._session.scalar(
            select(Memory).where(Memory.category == cat.value, Memory.key == key)
        )
        if existing is None:
            row = Memory(
                id=str(uuid4()),
                category=cat.value,
                key=key,
                value=value,
                created_at=now,
                updated_at=now,
            )
            self._session.add(row)
        else:
            row = existing
            row.value = value
            row.updated_at = now
        self._session.flush()
        return _to_record(row)

    def get(self, category: str, key: str) -> MemoryRecord:
        cat = _parse_category(category)
        key = _normalize_key(key)
        row = self._session.scalar(
            select(Memory).where(Memory.category == cat.value, Memory.key == key)
        )
        if row is None:
            raise MemoryNotFoundError(
                f"No memory stored for category={cat.value} key={key!r}. "
                "Use `jarvis memory list` to see what is saved, or set the key first."
            )
        return _to_record(row)

    def list(self, category: str) -> list[MemoryRecord]:
        cat = _parse_category(category)
        rows = self._session.scalars(
            select(Memory)
            .where(Memory.category == cat.value)
            .order_by(Memory.key)
        ).all()
        return [_to_record(row) for row in rows]

    def delete(self, category: str, key: str) -> MemoryRecord:
        record = self.get(category, key)
        row = self._session.scalar(
            select(Memory).where(Memory.id == record.id)
        )
        if row is None:
            raise MemoryNotFoundError(
                f"No memory stored for category={record.category.value} "
                f"key={record.key!r}."
            )
        self._session.delete(row)
        self._session.flush()
        return record
