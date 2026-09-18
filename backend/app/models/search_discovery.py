from sqlalchemy import (
    Column, DateTime, ForeignKey, Index, Integer, JSON, String, Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, utc_now


class SearchQuery(Base):
    __tablename__ = "search_queries"

    id = Column(Integer, primary_key=True)
    brand_id = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String(50), nullable=False, index=True)
    query = Column(Text, nullable=False)
    category = Column(String(100), nullable=False, index=True)
    product = Column(String(255), nullable=True, index=True)
    competitor = Column(String(255), nullable=True, index=True)
    country = Column(String(10), default="US", nullable=False)
    language = Column(String(20), default="en", nullable=False)
    enabled = Column(Integer, default=1, nullable=False)
    last_run_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    runs = relationship("SearchRun", back_populates="query_record", cascade="all, delete-orphan")
    results = relationship("SearchResult", back_populates="query_record", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint(
            "brand_id", "provider", "query", "country", "language",
            name="uq_search_query_scope",
        ),
    )


class SearchRun(Base):
    __tablename__ = "search_runs"

    id = Column(Integer, primary_key=True)
    query_id = Column(Integer, ForeignKey("search_queries.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String(50), nullable=False, index=True)
    started_at = Column(DateTime, default=utc_now, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(50), default="running", nullable=False, index=True)
    results_found = Column(Integer, default=0, nullable=False)
    results_new = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)

    query_record = relationship("SearchQuery", back_populates="runs")
    results = relationship("SearchResult", back_populates="search_run")


class SearchResult(Base):
    __tablename__ = "search_results"

    id = Column(Integer, primary_key=True)
    query_id = Column(Integer, ForeignKey("search_queries.id", ondelete="CASCADE"), nullable=False, index=True)
    search_run_id = Column(Integer, ForeignKey("search_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    provider = Column(String(50), nullable=False, index=True)
    title = Column(Text, nullable=True)
    snippet = Column(Text, nullable=True)
    url = Column(Text, nullable=False)
    display_domain = Column(String(255), nullable=True, index=True)
    position = Column(Integer, nullable=True)
    published_at = Column(DateTime, nullable=True)
    country = Column(String(10), default="US", nullable=False)
    language = Column(String(20), default="en", nullable=False)
    discovered_at = Column(DateTime, default=utc_now, nullable=False)
    last_seen_at = Column(DateTime, default=utc_now, nullable=False)
    raw_metadata = Column(JSON, default=dict, nullable=False)

    query_record = relationship("SearchQuery", back_populates="results")
    search_run = relationship("SearchRun", back_populates="results")

    __table_args__ = (
        UniqueConstraint("query_id", "url", name="uq_search_result_query_url"),
        Index("ix_search_results_query_seen", "query_id", "last_seen_at"),
    )
