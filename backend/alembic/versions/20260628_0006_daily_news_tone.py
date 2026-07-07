"""daily_news_tone table (GDELT news sentiment)

Revision ID: 20260628_0006
Revises: 20260625_0005
Create Date: 2026-06-28
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260628_0006"
down_revision: str | None = "20260625_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "daily_news_tone",
        sa.Column("query_key", sa.String(32), primary_key=True),
        sa.Column("day", sa.DateTime(timezone=True), primary_key=True),
        sa.Column("tone", sa.Numeric(8, 4), nullable=False),
        sa.Column("volume", sa.Numeric(10, 6), nullable=False),
        sa.Column("article_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("source", sa.String(32), nullable=False, server_default="gdelt"),
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
    op.create_index("ix_daily_news_tone_day", "daily_news_tone", ["query_key", sa.text("day DESC")])


def downgrade() -> None:
    op.drop_index("ix_daily_news_tone_day", table_name="daily_news_tone")
    op.drop_table("daily_news_tone")
