"""macro_series table (FRED macro / FX-driver cache)

Revision ID: 20260704_0008
Revises: 20260702_0007
Create Date: 2026-07-04
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260704_0008"
down_revision: str | None = "20260702_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "macro_series",
        sa.Column("series_id", sa.String(32), primary_key=True),
        sa.Column("day", sa.DateTime(timezone=True), primary_key=True),
        sa.Column("value", sa.Numeric(18, 6), nullable=False),
        sa.Column("source", sa.String(32), nullable=False, server_default="fred"),
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
    )
    op.create_index("ix_macro_series_day", "macro_series", ["series_id", sa.text("day DESC")])


def downgrade() -> None:
    op.drop_index("ix_macro_series_day", table_name="macro_series")
    op.drop_table("macro_series")
