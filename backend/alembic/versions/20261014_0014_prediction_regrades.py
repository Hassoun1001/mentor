"""Prediction re-grades: the audit log behind correcting graded outcomes.

Additive only — one new table, nothing existing is touched.

The resolver used to grade a call from the bar before its horizon whenever
the horizon bar was not stored yet. Re-grading puts each outcome on its own
finished bar; every change writes the replaced values here first, so it is
auditable and reversible. See ``mentor/application/forecasting/regrade.py``.

Revision ID: 20261014_0014
Revises: 20261013_0013
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "20261014_0014"
down_revision: str | None = "20261013_0013"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "prediction_regrades",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("batch_id", sa.String(64), nullable=False),
        sa.Column("prediction_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("old_realised_close", sa.Numeric(20, 8), nullable=False),
        sa.Column("old_realised_outcome", sa.Integer(), nullable=False),
        sa.Column("new_realised_close", sa.Numeric(20, 8), nullable=False),
        sa.Column("new_realised_outcome", sa.Integer(), nullable=False),
        sa.Column("outcome_bar_ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("regraded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reverted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_prediction_regrades_batch", "prediction_regrades", ["batch_id"])
    op.create_index(
        "ix_prediction_regrades_prediction", "prediction_regrades", ["prediction_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_prediction_regrades_prediction", table_name="prediction_regrades")
    op.drop_index("ix_prediction_regrades_batch", table_name="prediction_regrades")
    op.drop_table("prediction_regrades")
