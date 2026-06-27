"""initial schema — price_bars (hypertable), trades, journal_reflections

Revision ID: 20260625_0001
Revises:
Create Date: 2026-06-25
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260625_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # TimescaleDB extension — created only if the binary is available on this
    # server. On plain Postgres the price_bars table stays a regular table
    # with the same schema and index; the app behaves identically for one
    # instrument's worth of data. The DO block swallows the absence cleanly.
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_available_extensions WHERE name = 'timescaledb') THEN
                CREATE EXTENSION IF NOT EXISTS timescaledb;
            END IF;
        END
        $$;
        """
    )

    op.create_table(
        "price_bars",
        sa.Column("symbol", sa.String(16), primary_key=True),
        sa.Column("timeframe", sa.String(8), primary_key=True),
        sa.Column("ts", sa.DateTime(timezone=True), primary_key=True),
        sa.Column("open", sa.Numeric(20, 8), nullable=False),
        sa.Column("high", sa.Numeric(20, 8), nullable=False),
        sa.Column("low", sa.Numeric(20, 8), nullable=False),
        sa.Column("close", sa.Numeric(20, 8), nullable=False),
        sa.Column("volume", sa.Numeric(20, 4), nullable=True),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column(
            "ingested_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("high >= low", name="ck_price_bars_high_ge_low"),
        sa.CheckConstraint("high >= open AND high >= close", name="ck_price_bars_high_envelope"),
        sa.CheckConstraint("low <= open AND low <= close", name="ck_price_bars_low_envelope"),
    )
    op.create_index(
        "ix_price_bars_symbol_ts_desc",
        "price_bars",
        ["symbol", "timeframe", sa.text("ts DESC")],
    )

    # Convert to a hypertable *only if* TimescaleDB is installed. On plain
    # Postgres this is a no-op and price_bars remains an ordinary table.
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'timescaledb') THEN
                PERFORM create_hypertable(
                    'price_bars', 'ts',
                    chunk_time_interval => INTERVAL '7 days',
                    if_not_exists => TRUE, migrate_data => TRUE
                );
            END IF;
        END
        $$;
        """
    )

    op.create_table(
        "trades",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("symbol", sa.String(16), nullable=False),
        sa.Column("direction", sa.String(8), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="planned"),
        sa.Column("size_lots", sa.Numeric(12, 4), nullable=False),
        sa.Column("planned_entry", sa.Numeric(20, 8), nullable=False),
        sa.Column("planned_stop", sa.Numeric(20, 8), nullable=False),
        sa.Column("planned_target", sa.Numeric(20, 8), nullable=True),
        sa.Column("actual_entry", sa.Numeric(20, 8), nullable=True),
        sa.Column("actual_exit", sa.Numeric(20, 8), nullable=True),
        sa.Column("entry_ts", sa.DateTime(timezone=True), nullable=True),
        sa.Column("exit_ts", sa.DateTime(timezone=True), nullable=True),
        sa.Column("initial_risk_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("risk_currency", sa.String(3), nullable=False),
        sa.Column("realised_pnl", sa.Numeric(18, 2), nullable=True),
        sa.Column("realised_r", sa.Numeric(8, 4), nullable=True),
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
        sa.CheckConstraint("direction IN ('long','short')", name="ck_trades_direction"),
        sa.CheckConstraint(
            "status IN ('planned','open','closed','cancelled')",
            name="ck_trades_status",
        ),
        sa.CheckConstraint("size_lots >= 0", name="ck_trades_size_nonneg"),
        sa.CheckConstraint(
            "planned_entry > 0 AND planned_stop > 0",
            name="ck_trades_prices_positive",
        ),
    )
    op.create_index(
        "ix_trades_symbol_status_created",
        "trades",
        ["symbol", "status", "created_at"],
    )

    op.create_table(
        "journal_reflections",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "trade_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("trades.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column(
            "mistake_tags",
            postgresql.ARRAY(sa.String(32)),
            server_default="{}",
            nullable=False,
        ),
        sa.Column("emotion", sa.String(32), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
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


def downgrade() -> None:
    op.drop_table("journal_reflections")
    op.drop_index("ix_trades_symbol_status_created", table_name="trades")
    op.drop_table("trades")
    op.drop_index("ix_price_bars_symbol_ts_desc", table_name="price_bars")
    op.drop_table("price_bars")
