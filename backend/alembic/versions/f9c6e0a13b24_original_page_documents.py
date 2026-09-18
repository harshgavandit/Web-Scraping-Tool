"""Add original public document evidence and snapshots.

Revision ID: f9c6e0a13b24
Revises: e8b5d9f02a13
"""

from alembic import op
import sqlalchemy as sa


revision = "f9c6e0a13b24"
down_revision = "e8b5d9f02a13"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("post_id", sa.Integer(), sa.ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("canonical_url", sa.Text()),
        sa.Column("domain", sa.String(255)),
        sa.Column("source_type", sa.String(50), nullable=False, server_default="article"),
        sa.Column("content_status", sa.String(50), nullable=False, server_default="snippet_only"),
        sa.Column("robots_allowed", sa.Boolean()),
        sa.Column("http_status", sa.Integer()),
        sa.Column("language", sa.String(20)),
        sa.Column("publisher", sa.String(255)),
        sa.Column("author", sa.String(255)),
        sa.Column("fetched_at", sa.DateTime(), nullable=False),
        sa.Column("error_message", sa.Text()),
    )
    op.create_index("ix_documents_post_id", "documents", ["post_id"], unique=True)
    op.create_index("ix_documents_domain", "documents", ["domain"])
    op.create_index("ix_documents_source_type", "documents", ["source_type"])
    op.create_index("ix_documents_content_status", "documents", ["content_status"])
    op.create_table(
        "document_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content_text", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("extracted_data", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_document_snapshots_document_id", "document_snapshots", ["document_id"])
    op.create_index("ix_document_snapshots_content_hash", "document_snapshots", ["content_hash"])


def downgrade() -> None:
    op.drop_table("document_snapshots")
    op.drop_table("documents")
