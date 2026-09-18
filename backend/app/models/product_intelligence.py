from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.models.base import Base, utc_now


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    brand_id = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    family = Column(String(255), nullable=True)
    category = Column(String(100), nullable=True)
    aliases = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    evidence = relationship("MentionEvidence", back_populates="product")
    issue_clusters = relationship("IssueCluster", back_populates="product")

    __table_args__ = (UniqueConstraint("brand_id", "name", name="uq_product_brand_name"),)


class MentionEvidence(Base):
    __tablename__ = "mention_evidence"

    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)
    aspect = Column(String(100), nullable=False, index=True)
    sentiment = Column(String(50), nullable=False, index=True)
    sentiment_score = Column(Float, default=0.0, nullable=False)
    evidence_quote = Column(Text, nullable=False)
    confidence = Column(Float, default=0.0, nullable=False)
    extraction_method = Column(String(50), default="rules_v1", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    product = relationship("Product", back_populates="evidence")

    __table_args__ = (Index("ix_mention_evidence_post_aspect", "post_id", "aspect"),)


class IssueCluster(Base):
    __tablename__ = "issue_clusters"

    id = Column(Integer, primary_key=True)
    brand_id = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    aspect = Column(String(100), nullable=False, index=True)
    sentiment = Column(String(50), default="Negative", nullable=False)
    mention_count = Column(Integer, default=0, nullable=False)
    unique_sources = Column(Integer, default=0, nullable=False)
    growth_pct = Column(Float, default=0.0, nullable=False)
    attention_score = Column(Float, default=0.0, nullable=False)
    risk_score = Column(Float, default=0.0, nullable=False, index=True)
    risk_level = Column(String(50), default="Monitor", nullable=False, index=True)
    confidence = Column(Float, default=0.0, nullable=False)
    first_seen_at = Column(DateTime, nullable=True)
    last_seen_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=utc_now, nullable=False)

    product = relationship("Product", back_populates="issue_clusters")

    __table_args__ = (UniqueConstraint("brand_id", "product_id", "aspect", name="uq_issue_cluster_product_aspect"),)
