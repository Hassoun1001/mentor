"""stock_tips table (tipster track record)

Revision ID: 20260702_0007
Revises: 20260628_0006
Create Date: 2026-07-02
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260702_0007"
down_revision: str | None = "20260628_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "stock_tips",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tipster", sa.String(64), nullable=False),
        sa.Column("ticker", sa.String(16), nullable=False),
        sa.Column("category", sa.String(24), nullable=False),
        sa.Column("action", sa.String(16), nullable=False),
        sa.Column("conviction", sa.String(8), nullable=False),
        sa.Column("note", sa.Text, nullable=False, server_default=""),
        sa.Column("raw_message", sa.Text, nullable=True),
        sa.Column("mentioned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("mention_price", sa.Numeric(20, 6), nullable=True),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("source", sa.String(16), nullable=False, server_default="yahoo"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "action IN ('buy','buy_on_dip','hold','watch','avoid')",
            name="ck_stock_tips_action",
        ),
    )
    op.create_index("ix_stock_tips_tipster_ticker", "stock_tips", ["tipster", "ticker"])
    op.create_index(
        "ix_stock_tips_mentioned_at", "stock_tips", [sa.text("mentioned_at DESC")]
    )


def downgrade() -> None:
    op.drop_index("ix_stock_tips_mentioned_at", table_name="stock_tips")
    op.drop_index("ix_stock_tips_tipster_ticker", table_name="stock_tips")
    op.drop_table("stock_tips")
