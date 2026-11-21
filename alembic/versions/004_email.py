"""Cached inbox messages for the email agent.

Revision ID: 004_email
Revises: 003_m5_m6_work
Create Date: 2026-11-21
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004_email"
down_revision: Union[str, Sequence[str], None] = "003_m5_m6_work"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "emails",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("internet_id", sa.String(length=512), nullable=False),
        sa.Column("from_addr", sa.String(length=512), nullable=False),
        sa.Column("to_addr", sa.String(length=512), nullable=False),
        sa.Column("subject", sa.String(length=512), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("received_at", sa.DateTime(), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=True),
        sa.Column("urgency", sa.String(length=16), nullable=True),
        sa.Column("deadline_note", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("draft_reply", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("internet_id", name="uq_emails_internet_id"),
    )
    op.create_index("ix_emails_received_at", "emails", ["received_at"])
    op.create_index("ix_emails_category", "emails", ["category"])


def downgrade() -> None:
    op.drop_index("ix_emails_category", table_name="emails")
    op.drop_index("ix_emails_received_at", table_name="emails")
    op.drop_table("emails")
