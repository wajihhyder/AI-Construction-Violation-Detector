"""add tracking_id to violations_report

Revision ID: 20260504000000
Revises:
Create Date: 2026-05-04

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260504000000"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if "violations_report" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("violations_report")}
    if "tracking_id" in cols:
        return
    with op.batch_alter_table("violations_report") as batch_op:
        batch_op.add_column(sa.Column("tracking_id", sa.String(length=40), nullable=True))
    op.execute(
        sa.text(
            "UPDATE violations_report SET tracking_id = "
            "'VS-' || strftime('%Y%m%d', submission_date) || '-' || printf('%05d', report_id) "
            "WHERE tracking_id IS NULL OR tracking_id = ''"
        )
    )
    op.create_index(
        op.f("ix_violations_report_tracking_id"),
        "violations_report",
        ["tracking_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_violations_report_tracking_id"), table_name="violations_report")
    with op.batch_alter_table("violations_report") as batch_op:
        batch_op.drop_column("tracking_id")
