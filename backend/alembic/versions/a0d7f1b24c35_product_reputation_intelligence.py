"""Add product, aspect evidence, attention, and reputation intelligence.

Revision ID: a0d7f1b24c35
Revises: f9c6e0a13b24
"""

from alembic import op
import sqlalchemy as sa


revision = "a0d7f1b24c35"
down_revision = "f9c6e0a13b24"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("post_analysis", sa.Column("attention_score", sa.Float(), nullable=False, server_default="0"))
    op.add_column("post_analysis", sa.Column("attention_level", sa.String(50), nullable=False, server_default="Low attention"))
    op.add_column("post_analysis", sa.Column("attention_reasons", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("post_analysis", sa.Column("reputation_risk_score", sa.Float(), nullable=False, server_default="0"))
    op.add_column("post_analysis", sa.Column("reputation_risk_level", sa.String(50), nullable=False, server_default="Monitor"))
    op.create_index("ix_post_analysis_attention_score", "post_analysis", ["attention_score"])
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("brand_id", sa.Integer(), sa.ForeignKey("brands.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("family", sa.String(255)),
        sa.Column("category", sa.String(100)),
        sa.Column("aliases", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("brand_id", "name", name="uq_product_brand_name"),
    )
    op.create_index("ix_products_brand_id", "products", ["brand_id"])
    op.create_index("ix_products_name", "products", ["name"])
    op.create_table(
        "mention_evidence",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("post_id", sa.Integer(), sa.ForeignKey("posts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="SET NULL")),
        sa.Column("aspect", sa.String(100), nullable=False),
        sa.Column("sentiment", sa.String(50), nullable=False),
        sa.Column("sentiment_score", sa.Float(), nullable=False),
        sa.Column("evidence_quote", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("extraction_method", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_mention_evidence_post_id", "mention_evidence", ["post_id"])
    op.create_index("ix_mention_evidence_product_id", "mention_evidence", ["product_id"])
    op.create_index("ix_mention_evidence_aspect", "mention_evidence", ["aspect"])
    op.create_index("ix_mention_evidence_sentiment", "mention_evidence", ["sentiment"])
    op.create_index("ix_mention_evidence_post_aspect", "mention_evidence", ["post_id", "aspect"])
    op.create_table(
        "issue_clusters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("brand_id", sa.Integer(), sa.ForeignKey("brands.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="SET NULL")),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("aspect", sa.String(100), nullable=False),
        sa.Column("sentiment", sa.String(50), nullable=False),
        sa.Column("mention_count", sa.Integer(), nullable=False),
        sa.Column("unique_sources", sa.Integer(), nullable=False),
        sa.Column("growth_pct", sa.Float(), nullable=False),
        sa.Column("attention_score", sa.Float(), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("risk_level", sa.String(50), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("first_seen_at", sa.DateTime()),
        sa.Column("last_seen_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("brand_id", "product_id", "aspect", name="uq_issue_cluster_product_aspect"),
    )
    op.create_index("ix_issue_clusters_brand_id", "issue_clusters", ["brand_id"])
    op.create_index("ix_issue_clusters_product_id", "issue_clusters", ["product_id"])
    op.create_index("ix_issue_clusters_aspect", "issue_clusters", ["aspect"])
    op.create_index("ix_issue_clusters_risk_score", "issue_clusters", ["risk_score"])
    op.create_index("ix_issue_clusters_risk_level", "issue_clusters", ["risk_level"])


def downgrade() -> None:
    op.drop_table("issue_clusters")
    op.drop_table("mention_evidence")
    op.drop_table("products")
    op.drop_index("ix_post_analysis_attention_score", table_name="post_analysis")
    op.drop_column("post_analysis", "reputation_risk_level")
    op.drop_column("post_analysis", "reputation_risk_score")
    op.drop_column("post_analysis", "attention_reasons")
    op.drop_column("post_analysis", "attention_level")
    op.drop_column("post_analysis", "attention_score")
