"""alerts table

Revision ID: 20260625_0004
Revises: 20260625_0003
Create Date: 2026-06-25
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260625_0004"
down_revision: str | None = "20260625_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "alerts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("kind", sa.String(24), nullable=False),
        sa.Column("label", sa.Text, nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="armed"),
        sa.Column("condition_json", sa.Text, nullable=False),
        sa.Column("fired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_evaluated_at", sa.DateTime(timezone=True), nullable=True),
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
            "kind IN ('price_above','price_below','signal_change','event_freeze')",
            name="ck_alerts_kind",
        ),
        sa.CheckConstraint("status IN ('armed','fired','disabled')", name="ck_alerts_status"),
    )
    op.create_index("ix_alerts_status", "alerts", ["status"])


def downgrade() -> None:
    op.drop_index("ix_alerts_status", table_name="alerts")
    op.drop_table("alerts")
