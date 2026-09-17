"""Enforce content-hash deduplication at the database boundary.

Revision ID: b31e8d6c2a04
Revises: 9c2f7a1d4b60
"""

from typing import Sequence, Union

from alembic import op


revision: str = "b31e8d6c2a04"
down_revision: Union[str, Sequence[str], None] = "9c2f7a1d4b60"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("posts") as batch_op:
        batch_op.create_unique_constraint("uq_posts_content_hash", ["content_hash"])


def downgrade() -> None:
    with op.batch_alter_table("posts") as batch_op:
        batch_op.drop_constraint("uq_posts_content_hash", type_="unique")
