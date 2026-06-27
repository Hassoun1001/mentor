"""curriculum progress table

Revision ID: 20260625_0002
Revises: 20260625_0001
Create Date: 2026-06-25
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260625_0002"
down_revision: str | None = "20260625_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "lesson_progress",
        sa.Column("lesson_slug", sa.String(128), primary_key=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="in_progress"),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('not_started','in_progress','completed')",
            name="ck_lesson_progress_status",
        ),
    )


def downgrade() -> None:
    op.drop_table("lesson_progress")
