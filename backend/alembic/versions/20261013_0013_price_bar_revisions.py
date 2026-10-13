"""Price-bar revisions: the audit log behind correcting provisional bars.

Additive only — one new table, nothing existing is touched.

Ingestion used to store the bar still forming and never update it. The
fix replaces such a bar with its settled version, and every replacement
(or operator removal) writes the old values here first, so each change is
auditable and reversible. See ``mentor/domain/market/settlement.py``.

Revision ID: 20261013_0013
Revises: 20261013_0012
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "20261013_0013"
down_revision: str | None = "20261013_0012"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "price_bar_revisions",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("batch_id", sa.String(64), nullable=False),
        sa.Column("action", sa.String(16), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("symbol", sa.String(16), nullable=False),
        sa.Column("timeframe", sa.String(8), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("old_open", sa.Numeric(20, 8), nullable=False),
        sa.Column("old_high", sa.Numeric(20, 8), nullable=False),
        sa.Column("old_low", sa.Numeric(20, 8), nullable=False),
        sa.Column("old_close", sa.Numeric(20, 8), nullable=False),
        sa.Column("old_volume", sa.Numeric(20, 4), nullable=True),
        sa.Column("old_source", sa.String(32), nullable=False),
        sa.Column("old_ingested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("new_open", sa.Numeric(20, 8), nullable=True),
        sa.Column("new_high", sa.Numeric(20, 8), nullable=True),
        sa.Column("new_low", sa.Numeric(20, 8), nullable=True),
        sa.Column("new_close", sa.Numeric(20, 8), nullable=True),
        sa.Column("new_volume", sa.Numeric(20, 4), nullable=True),
        sa.Column("new_source", sa.String(32), nullable=True),
        sa.Column("revised_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reverted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "action IN ('corrected','removed')", name="ck_price_bar_revisions_action"
        ),
    )
    op.create_index("ix_price_bar_revisions_batch", "price_bar_revisions", ["batch_id"])
    op.create_index(
        "ix_price_bar_revisions_bar", "price_bar_revisions", ["symbol", "timeframe", "ts"]
    )


def downgrade() -> None:
    op.drop_index("ix_price_bar_revisions_bar", table_name="price_bar_revisions")
    op.drop_index("ix_price_bar_revisions_batch", table_name="price_bar_revisions")
    op.drop_table("price_bar_revisions")
