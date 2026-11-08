"""Allow a prediction to be voided.

A call made from a bar printed while the market was closed started from a
price no broker offered. It leaves the live record but stays in the table.
Widens one check constraint; no row changes.

Revision ID: 20261108_0016
Revises: 20261108_0015
"""

from __future__ import annotations

from alembic import op

revision: str = "20261108_0016"
down_revision: str | None = "20261108_0015"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.drop_constraint("ck_predictions_origin", "predictions", type_="check")
    op.create_check_constraint(
        "ck_predictions_origin",
        "predictions",
        "origin IN ('live','replay','voided')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_predictions_origin", "predictions", type_="check")
    op.create_check_constraint(
        "ck_predictions_origin",
        "predictions",
        "origin IN ('live','replay')",
    )
