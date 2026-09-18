"""Add Google discovery query, run, and result audit tables.

Revision ID: e8b5d9f02a13
Revises: d7a4c8e91f02
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e8b5d9f02a13"
down_revision: Union[str, Sequence[str], None] = "d7a4c8e91f02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "search_queries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("brand_id", sa.Integer(), sa.ForeignKey("brands.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("product", sa.String(255)),
        sa.Column("competitor", sa.String(255)),
        sa.Column("country", sa.String(10), nullable=False, server_default="US"),
        sa.Column("language", sa.String(20), nullable=False, server_default="en"),
        sa.Column("enabled", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("last_run_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("brand_id", "provider", "query", "country", "language", name="uq_search_query_scope"),
    )
    op.create_index("ix_search_queries_brand_id", "search_queries", ["brand_id"])
    op.create_index("ix_search_queries_provider", "search_queries", ["provider"])
    op.create_index("ix_search_queries_category", "search_queries", ["category"])
    op.create_index("ix_search_queries_product", "search_queries", ["product"])
    op.create_index("ix_search_queries_competitor", "search_queries", ["competitor"])

    op.create_table(
        "search_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("query_id", sa.Integer(), sa.ForeignKey("search_queries.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime()),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("results_found", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("results_new", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text()),
    )
    op.create_index("ix_search_runs_query_id", "search_runs", ["query_id"])
    op.create_index("ix_search_runs_provider", "search_runs", ["provider"])
    op.create_index("ix_search_runs_status", "search_runs", ["status"])

    op.create_table(
        "search_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("query_id", sa.Integer(), sa.ForeignKey("search_queries.id", ondelete="CASCADE"), nullable=False),
        sa.Column("search_run_id", sa.Integer(), sa.ForeignKey("search_runs.id", ondelete="SET NULL")),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("title", sa.Text()),
        sa.Column("snippet", sa.Text()),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("display_domain", sa.String(255)),
        sa.Column("position", sa.Integer()),
        sa.Column("published_at", sa.DateTime()),
        sa.Column("country", sa.String(10), nullable=False, server_default="US"),
        sa.Column("language", sa.String(20), nullable=False, server_default="en"),
        sa.Column("discovered_at", sa.DateTime(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(), nullable=False),
        sa.Column("raw_metadata", sa.JSON(), nullable=False),
        sa.UniqueConstraint("query_id", "url", name="uq_search_result_query_url"),
    )
    op.create_index("ix_search_results_query_id", "search_results", ["query_id"])
    op.create_index("ix_search_results_search_run_id", "search_results", ["search_run_id"])
    op.create_index("ix_search_results_provider", "search_results", ["provider"])
    op.create_index("ix_search_results_display_domain", "search_results", ["display_domain"])
    op.create_index("ix_search_results_query_seen", "search_results", ["query_id", "last_seen_at"])


def downgrade() -> None:
    op.drop_table("search_results")
    op.drop_table("search_runs")
    op.drop_table("search_queries")
