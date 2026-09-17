from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.models.base import Base, utc_now


class PostAnalysis(Base):
    __tablename__ = "post_analysis"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    sentiment = Column(String(50), nullable=False, index=True)  # Positive, Negative, Neutral, Mixed
    sentiment_score = Column(Float, default=0.0, nullable=False)
    topic = Column(String(255), nullable=True, index=True)
    product = Column(String(255), nullable=True, index=True)
    competitor = Column(String(255), nullable=True, index=True)
    key_positive = Column(Text, nullable=True)
    key_negative = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)
    virality_score = Column(Float, default=0.0, nullable=False, index=True)
    virality_level = Column(String(50), default="Low", nullable=False)  # Low, Medium, High, Viral
    is_viral = Column(Boolean, default=False, nullable=False, index=True)
    analyzed_at = Column(DateTime, default=utc_now, nullable=False)
    analysis_version = Column(String(50), default="1.0", nullable=False)
    model_used = Column(String(100), default="vader_local", nullable=False)

    post = relationship("Post", back_populates="analysis")

    __table_args__ = (
        Index("ix_post_analysis_sentiment_viral", "sentiment", "is_viral"),
        Index("ix_post_analysis_sentiment_score", "sentiment", "sentiment_score"),
        Index("ix_post_analysis_viral_score", "is_viral", "virality_score"),
    )
