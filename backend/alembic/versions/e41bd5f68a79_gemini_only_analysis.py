"""Remove legacy fallback analysis and enforce Gemini provenance.

Revision ID: e41bd5f68a79
Revises: d30ac4e57f68
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e41bd5f68a79"
down_revision: Union[str, Sequence[str], None] = "d30ac4e57f68"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text("""
        UPDATE post_analysis
        SET topic = NULL,
            product = NULL,
            competitor = NULL,
            key_positive = NULL,
            key_negative = NULL,
            summary = NULL,
            recommendation = NULL,
            model_used = 'gemini-3.8-flash',
            analysis_provider = 'gemini',
            analysis_status = 'pending'
        WHERE analysis_provider != 'gemini'
           OR analysis_status != 'completed'
    """))


def downgrade() -> None:
    # Removed synthetic analysis cannot be reconstructed safely.
    pass
