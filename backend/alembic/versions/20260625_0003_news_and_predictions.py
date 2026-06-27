"""news_items + predictions tables

Revision ID: 20260625_0003
Revises: 20260625_0002
Create Date: 2026-06-25
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260625_0003"
down_revision: str | None = "20260625_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "news_items",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("url", sa.Text, nullable=False),
        sa.Column("url_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("headline", sa.Text, nullable=False),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("category", sa.String(16), nullable=True),
        sa.Column("impact", sa.Numeric(4, 3), nullable=True),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=True),
        sa.Column("rationale", sa.Text, nullable=True),
        sa.Column("classified_at", sa.DateTime(timezone=True), nullable=True),
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
            "category IS NULL OR category IN "
            "('macro','regulatory','geopolitical','risk-off','hype','other')",
            name="ck_news_items_category",
        ),
    )
    op.create_index("ix_news_items_ts_desc", "news_items", [sa.text("ts DESC")])

    op.create_table(
        "predictions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("symbol", sa.String(16), nullable=False),
        sa.Column("timeframe", sa.String(8), nullable=False),
        sa.Column("asof", sa.DateTime(timezone=True), nullable=False),
        sa.Column("asof_close", sa.Numeric(20, 8), nullable=False),
        sa.Column("horizon_bars", sa.Integer, nullable=False),
        sa.Column("horizon_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("model_name", sa.String(128), nullable=False),
        sa.Column("p_up", sa.Numeric(6, 4), nullable=False),
        sa.Column("confidence", sa.Numeric(6, 4), nullable=False),
        sa.Column("direction", sa.String(8), nullable=False),
        sa.Column("reasoning", sa.Text, nullable=False),
        sa.Column("features_json", sa.Text, nullable=False),
        sa.Column("realised_close", sa.Numeric(20, 8), nullable=True),
        sa.Column("realised_outcome", sa.Integer, nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
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
            "direction IN ('long','short','neutral')", name="ck_predictions_direction"
        ),
        sa.CheckConstraint("p_up >= 0 AND p_up <= 1", name="ck_predictions_p_up"),
    )
    op.create_index("ix_predictions_symbol_asof", "predictions", ["symbol", sa.text("asof DESC")])
    op.create_index("ix_predictions_unresolved", "predictions", ["horizon_at", "resolved_at"])


def downgrade() -> None:
    op.drop_index("ix_predictions_unresolved", table_name="predictions")
    op.drop_index("ix_predictions_symbol_asof", table_name="predictions")
    op.drop_table("predictions")
    op.drop_index("ix_news_items_ts_desc", table_name="news_items")
    op.drop_table("news_items")
