from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, DateTime, ForeignKey,
    UniqueConstraint, Index, JSON
)
from sqlalchemy.orm import relationship
from app.models.base import Base, utc_now


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True)
    source = Column(String(50), nullable=False, index=True)
    external_id = Column(String(255), nullable=True)
    url = Column(Text, nullable=True)
    author = Column(String(255), nullable=True)
    title = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    published_at = Column(DateTime, nullable=True, index=True)
    collected_at = Column(DateTime, default=utc_now, nullable=False)
    likes = Column(Integer, default=0, nullable=False)
    comments = Column(Integer, default=0, nullable=False)
    shares = Column(Integer, default=0, nullable=False)
    engagement_count = Column(Integer, default=0, nullable=False)
    engagement_velocity = Column(Float, default=0.0, nullable=False)
    raw_metadata = Column(JSON, default=dict, nullable=False)
    content_hash = Column(String(64), index=True, nullable=False)

    brand = relationship("Brand", back_populates="posts")
    analysis = relationship("PostAnalysis", back_populates="post", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_source_external_id"),
        UniqueConstraint("content_hash", name="uq_posts_content_hash"),
        Index("ix_posts_brand_published", "brand_id", "published_at"),
        Index("ix_posts_source_brand", "source", "brand_id"),
        Index("ix_posts_brand_engagement", "brand_id", "engagement_count"),
    )
