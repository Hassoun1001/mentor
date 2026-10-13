"""Record the model's own probability when a live correction restates it.

Live recalibration restates the champion's ``p_up`` once its live record
shows it has been over- or underconfident. The next live fit must learn
from what the *model* said, not from the previously corrected number — or
each correction would be fitted on top of the last and they would stack.

Nullable, with no backfill: before this column existed no correction was
ever applied, so for every existing row ``p_up`` already is the model's own.

Revision ID: 20261013_0011
Revises: 20260723_0010
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "20261013_0011"
down_revision: str | None = "20260723_0010"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column(
        "predictions",
        sa.Column("p_up_model", sa.Numeric(precision=6, scale=4), nullable=True),
    )
    op.create_check_constraint(
        "ck_predictions_p_up_model",
        "predictions",
        "p_up_model IS NULL OR (p_up_model >= 0 AND p_up_model <= 1)",
    )


def downgrade() -> None:
    op.drop_constraint("ck_predictions_p_up_model", "predictions", type_="check")
    op.drop_column("predictions", "p_up_model")
