"""Strategy lab: the trial ledger, candidates, paper positions and their history.

Additive only — four new tables, nothing existing is touched.

``strategy_trials`` is the multiple-testing ledger. It is append-only by
design (the application has no path that updates or deletes a row): the
bar every candidate must clear rises with its row count, so forgetting a
failed trial would quietly lower it.

Revision ID: 20261013_0012
Revises: 20261013_0011
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "20261013_0012"
down_revision: str | None = "20261013_0011"
branch_labels: str | None = None
depends_on: str | None = None


def _timestamps() -> list[sa.Column[object]]:
    return [
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "strategy_trials",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("config_key", sa.String(128), nullable=False, unique=True),
        sa.Column("candidate_key", sa.String(64), nullable=False),
        sa.Column("family", sa.String(48), nullable=False),
        sa.Column("timeframe", sa.String(8), nullable=False),
        sa.Column("params_json", sa.Text(), nullable=False),
        sa.Column("n_trades", sa.Integer(), nullable=False),
        sa.Column("mean_r", sa.Float(), nullable=False),
        sa.Column("sd_r", sa.Float(), nullable=False),
        sa.Column("t_stat", sa.Float(), nullable=False),
        sa.Column("dev_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dev_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "recorded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_strategy_trials_candidate", "strategy_trials", ["candidate_key"])

    op.create_table(
        "strategy_candidates",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("key", sa.String(64), nullable=False, unique=True),
        sa.Column("family", sa.String(48), nullable=False),
        sa.Column("timeframe", sa.String(8), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("hypothesis", sa.Text(), nullable=False),
        sa.Column("fingerprint", sa.String(32), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("status_reason", sa.Text(), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("n_trials_at_evaluation", sa.Integer(), nullable=False),
        sa.Column("plan_json", sa.Text(), nullable=True),
        sa.Column("evidence_json", sa.Text(), nullable=False),
        sa.Column("paper_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_bar_ts", sa.DateTime(timezone=True), nullable=True),
        sa.Column("live_looks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("promoted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("demoted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retired_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
        sa.CheckConstraint(
            "status IN ('rejected','paper','recommended','demoted','retired')",
            name="ck_strategy_candidates_status",
        ),
    )

    op.create_table(
        "paper_positions",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "candidate_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("strategy_candidates.id"),
            nullable=False,
        ),
        sa.Column("status", sa.String(12), nullable=False),
        sa.Column("direction", sa.String(8), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("signal_ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("stop_price", sa.Numeric(20, 8), nullable=False),
        sa.Column("target_price", sa.Numeric(20, 8), nullable=True),
        sa.Column("suggested_lots", sa.Numeric(12, 2), nullable=True),
        sa.Column("entry_ts", sa.DateTime(timezone=True), nullable=True),
        sa.Column("entry_price", sa.Numeric(20, 8), nullable=True),
        sa.Column("bars_held", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("exit_ts", sa.DateTime(timezone=True), nullable=True),
        sa.Column("exit_price", sa.Numeric(20, 8), nullable=True),
        sa.Column("exit_reason", sa.String(16), nullable=True),
        sa.Column("realised_r", sa.Numeric(10, 4), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        *_timestamps(),
        sa.CheckConstraint(
            "status IN ('pending','open','closed','cancelled')", name="ck_paper_positions_status"
        ),
        sa.CheckConstraint("direction IN ('long','short')", name="ck_paper_positions_direction"),
        sa.UniqueConstraint("candidate_id", "signal_ts", name="uq_paper_positions_signal"),
    )
    op.create_index(
        "ix_paper_positions_candidate_status", "paper_positions", ["candidate_id", "status"]
    )

    op.create_table(
        "strategy_events",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("candidate_key", sa.String(64), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "kind IN ('rejected','paper','promoted','demoted','retired')",
            name="ck_strategy_events_kind",
        ),
    )
    op.create_index("ix_strategy_events_at", "strategy_events", [sa.text("at DESC")])


def downgrade() -> None:
    op.drop_index("ix_strategy_events_at", table_name="strategy_events")
    op.drop_table("strategy_events")
    op.drop_index("ix_paper_positions_candidate_status", table_name="paper_positions")
    op.drop_table("paper_positions")
    op.drop_table("strategy_candidates")
    op.drop_index("ix_strategy_trials_candidate", table_name="strategy_trials")
    op.drop_table("strategy_trials")
