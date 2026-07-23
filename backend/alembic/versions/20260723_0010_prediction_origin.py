"""Record whether a prediction was made live or replayed from history.

Replayed predictions were written into the same table as live ones with
nothing to tell them apart. Every honest number the app reports — paper
P&L, calibration, the post-mortem, the significance verdicts — was
therefore one button click away from being quietly mixed with backfilled
history, with no way to separate them afterwards or even to know it had
happened.

Existing rows are stamped ``live``: the replayed batch was deleted by hand
earlier, so what remains is genuine forward prediction.

Revision ID: 20260723_0010
Revises: 20260716_0009
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "20260723_0010"
down_revision: str | None = "20260716_0009"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column(
        "predictions",
        sa.Column(
            "origin",
            sa.String(length=16),
            nullable=False,
            server_default="live",
        ),
    )
    op.create_check_constraint(
        "ck_predictions_origin",
        "predictions",
        "origin IN ('live','replay')",
    )
    # Every honest read filters on this, so it earns an index.
    op.create_index(
        "ix_predictions_origin_resolved",
        "predictions",
        ["origin", "resolved_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_predictions_origin_resolved", table_name="predictions")
    op.drop_constraint("ck_predictions_origin", "predictions", type_="check")
    op.drop_column("predictions", "origin")
