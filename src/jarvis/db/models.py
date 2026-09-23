"""SQLAlchemy models for Milestone 2 tables only.

Tasks, reminders, action logs, and confirmations arrive in later milestones.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Shared declarative base so Alembic can see every table."""


class Memory(Base):
    """One remembered fact, keyed by category + short name."""

    __tablename__ = "memories"
    __table_args__ = (
        UniqueConstraint("category", "key", name="uq_memories_category_key"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    key: Mapped[str] = mapped_column(String(256), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class ConversationMessage(Base):
    """One turn of chat, persisted so we can reload recent context later."""

    __tablename__ = "conversation_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, index=True
    )
