"""economic_events table

Revision ID: 20260625_0005
Revises: 20260625_0004
Create Date: 2026-06-25
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260625_0005"
down_revision: str | None = "20260625_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "economic_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("external_id", sa.String(64), nullable=False, unique=True),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("country", sa.String(8), nullable=False),
        sa.Column("impact", sa.Integer, nullable=False),
        sa.Column("forecast", sa.Text, nullable=True),
        sa.Column("previous", sa.Text, nullable=True),
        sa.Column("actual", sa.Text, nullable=True),
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
        sa.CheckConstraint("impact IN (1,2,3)", name="ck_economic_events_impact"),
    )
    op.create_index("ix_economic_events_ts", "economic_events", ["ts"])
    op.create_index("ix_economic_events_country_ts", "economic_events", ["country", "ts"])


def downgrade() -> None:
    op.drop_index("ix_economic_events_country_ts", table_name="economic_events")
    op.drop_index("ix_economic_events_ts", table_name="economic_events")
    op.drop_table("economic_events")
