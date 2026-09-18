"""Add email delivery state to reputation alerts.

Revision ID: d30ac4e57f68
Revises: c2f9b3d46e57
"""

from alembic import op
import sqlalchemy as sa


revision = "d30ac4e57f68"
down_revision = "c2f9b3d46e57"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("alerts", sa.Column("email_status", sa.String(50), nullable=False, server_default="pending"))
    op.add_column("alerts", sa.Column("email_recipients", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("alerts", sa.Column("email_sent_at", sa.DateTime()))
    op.add_column("alerts", sa.Column("email_error", sa.Text()))
    op.add_column("alerts", sa.Column("email_severity_sent", sa.String(50)))
    op.create_index("ix_alerts_email_status", "alerts", ["email_status"])


def downgrade() -> None:
    op.drop_index("ix_alerts_email_status", table_name="alerts")
    op.drop_column("alerts", "email_severity_sent")
    op.drop_column("alerts", "email_error")
    op.drop_column("alerts", "email_sent_at")
    op.drop_column("alerts", "email_recipients")
    op.drop_column("alerts", "email_status")
