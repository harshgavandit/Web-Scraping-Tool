"""Add enterprise alerts and AI provenance.

Revision ID: b1e8a2c35d46
Revises: a0d7f1b24c35
"""

from alembic import op
import sqlalchemy as sa


revision = "b1e8a2c35d46"
down_revision = "a0d7f1b24c35"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("post_analysis", sa.Column("analysis_provider", sa.String(50), nullable=False, server_default="local_heuristic"))
    op.add_column("post_analysis", sa.Column("analysis_status", sa.String(50), nullable=False, server_default="fallback"))
    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("brand_id", sa.Integer(), sa.ForeignKey("brands.id", ondelete="CASCADE"), nullable=False),
        sa.Column("issue_cluster_id", sa.Integer(), sa.ForeignKey("issue_clusters.id", ondelete="CASCADE"), nullable=False),
        sa.Column("alert_type", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("evidence_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("acknowledged_at", sa.DateTime()),
        sa.Column("resolved_at", sa.DateTime()),
        sa.UniqueConstraint("brand_id", "issue_cluster_id", name="uq_alert_brand_cluster"),
    )
    op.create_index("ix_alerts_brand_id", "alerts", ["brand_id"])
    op.create_index("ix_alerts_issue_cluster_id", "alerts", ["issue_cluster_id"])
    op.create_index("ix_alerts_severity", "alerts", ["severity"])
    op.create_index("ix_alerts_status", "alerts", ["status"])


def downgrade() -> None:
    op.drop_table("alerts")
    op.drop_column("post_analysis", "analysis_status")
    op.drop_column("post_analysis", "analysis_provider")
