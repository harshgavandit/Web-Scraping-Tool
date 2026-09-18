"""Add saved views for brand, category, and regional teams.

Revision ID: c2f9b3d46e57
Revises: b1e8a2c35d46
"""

from alembic import op
import sqlalchemy as sa


revision = "c2f9b3d46e57"
down_revision = "b1e8a2c35d46"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "saved_views",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("brand_id", sa.Integer(), sa.ForeignKey("brands.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("team", sa.String(100), nullable=False, server_default="brand"),
        sa.Column("filters", sa.JSON(), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_saved_views_brand_id", "saved_views", ["brand_id"])
    op.create_index("ix_saved_views_id", "saved_views", ["id"])


def downgrade() -> None:
    op.drop_table("saved_views")
