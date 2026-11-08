"""Trade plan snapshots: what the system said when a trade was logged from it.

Additive only — one new table, nothing existing is touched. The trigger
refuses updates so a saved plan can never be rewritten after the fact.
See ``mentor/domain/journal/system_plan.py``.

Revision ID: 20261108_0015
Revises: 20261014_0014
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "20261108_0015"
down_revision: str | None = "20261014_0014"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "trade_plan_snapshots",
        sa.Column(
            "trade_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("trades.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("symbol", sa.String(16), nullable=False),
        sa.Column("timeframe", sa.String(8), nullable=False),
        sa.Column("asof", sa.DateTime(timezone=True), nullable=False),
        sa.Column("model_name", sa.String(128), nullable=False),
        sa.Column("p_up", sa.Numeric(6, 4), nullable=False),
        sa.Column("confidence", sa.Numeric(6, 4), nullable=False),
        sa.Column("stance", sa.String(16), nullable=False),
        sa.Column("entry", sa.Numeric(20, 8), nullable=True),
        sa.Column("stop", sa.Numeric(20, 8), nullable=True),
        sa.Column("target", sa.Numeric(20, 8), nullable=True),
        sa.Column("reward_multiple", sa.Numeric(8, 4), nullable=True),
        sa.Column("horizon_bars", sa.Integer(), nullable=False),
        sa.Column("time_stop_deadline", sa.DateTime(timezone=True), nullable=False),
        sa.Column("prediction_id", sa.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "stance IN ('long','short','stand_aside')", name="ck_trade_plan_snapshots_stance"
        ),
    )
    op.execute(
        """
        CREATE FUNCTION trade_plan_snapshots_refuse_update() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'a saved trade plan cannot be changed';
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        """
        CREATE TRIGGER trade_plan_snapshots_no_update
        BEFORE UPDATE ON trade_plan_snapshots
        FOR EACH ROW EXECUTE FUNCTION trade_plan_snapshots_refuse_update()
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER trade_plan_snapshots_no_update ON trade_plan_snapshots")
    op.execute("DROP FUNCTION trade_plan_snapshots_refuse_update()")
    op.drop_table("trade_plan_snapshots")
