"""Add indexes for dashboard filters and sorting.

Revision ID: 9c2f7a1d4b60
Revises: 415fdc2ae1e8
"""

from typing import Sequence, Union

from alembic import op


revision: str = "9c2f7a1d4b60"
down_revision: Union[str, Sequence[str], None] = "415fdc2ae1e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_posts_brand_engagement", "posts", ["brand_id", "engagement_count"])
    op.create_index("ix_post_analysis_competitor", "post_analysis", ["competitor"])
    op.create_index("ix_post_analysis_product", "post_analysis", ["product"])
    op.create_index(
        "ix_post_analysis_sentiment_score",
        "post_analysis",
        ["sentiment", "sentiment_score"],
    )
    op.create_index(
        "ix_post_analysis_viral_score",
        "post_analysis",
        ["is_viral", "virality_score"],
    )


def downgrade() -> None:
    op.drop_index("ix_post_analysis_viral_score", table_name="post_analysis")
    op.drop_index("ix_post_analysis_sentiment_score", table_name="post_analysis")
    op.drop_index("ix_post_analysis_product", table_name="post_analysis")
    op.drop_index("ix_post_analysis_competitor", table_name="post_analysis")
    op.drop_index("ix_posts_brand_engagement", table_name="posts")
