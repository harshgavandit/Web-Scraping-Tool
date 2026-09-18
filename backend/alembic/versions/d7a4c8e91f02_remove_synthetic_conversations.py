"""Remove generated conversations and normalize unavailable engagement.

Revision ID: d7a4c8e91f02
Revises: b31e8d6c2a04
"""

from typing import Sequence, Union

from alembic import op


revision: str = "d7a4c8e91f02"
down_revision: Union[str, Sequence[str], None] = "b31e8d6c2a04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SYNTHETIC_POSTS = """
    url LIKE '%social.example.com%'
    OR external_id LIKE 'seed_%'
    OR external_id LIKE 'mock_%'
    OR external_id LIKE 'bulk_%'
"""


def upgrade() -> None:
    op.execute(f"DELETE FROM post_analysis WHERE post_id IN (SELECT id FROM posts WHERE {SYNTHETIC_POSTS})")
    op.execute(f"DELETE FROM posts WHERE {SYNTHETIC_POSTS}")
    op.execute("DELETE FROM collection_runs")

    op.execute("""
        UPDATE posts
        SET likes = 0,
            comments = 0,
            shares = 0,
            engagement_count = 0,
            engagement_velocity = 0
        WHERE source IN ('news_rss', 'web')
    """)
    op.execute("""
        UPDATE post_analysis
        SET virality_score = 0,
            virality_level = 'Low',
            is_viral = false
        WHERE post_id IN (
            SELECT id FROM posts WHERE source IN ('news_rss', 'web')
        )
    """)


def downgrade() -> None:
    # Generated conversations are intentionally not recoverable.
    pass
