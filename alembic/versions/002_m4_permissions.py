"""Action logs and pending confirmations.

Revision ID: 002_m4_permissions
Revises: 001_m2_memory
Create Date: 2026-10-24
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002_m4_permissions"
down_revision: Union[str, Sequence[str], None] = "001_m2_memory"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "action_logs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("agent", sa.String(length=64), nullable=False),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("permission_level", sa.Integer(), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("result", sa.String(length=32), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_action_logs_created_at", "action_logs", ["created_at"])

    op.create_table(
        "pending_confirmations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tool_name", sa.String(length=128), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("permission_level", sa.Integer(), nullable=False),
        sa.Column("agent", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pending_confirmations_status", "pending_confirmations", ["status"])


def downgrade() -> None:
    op.drop_index("ix_pending_confirmations_status", table_name="pending_confirmations")
    op.drop_table("pending_confirmations")
    op.drop_index("ix_action_logs_created_at", table_name="action_logs")
    op.drop_table("action_logs")
