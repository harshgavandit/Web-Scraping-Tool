from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base, utc_now


class TrackedKeyword(Base):
    __tablename__ = "tracked_keywords"

    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True)
    keyword = Column(String(255), nullable=False)
    category = Column(String(100), default="general", nullable=False)  # e.g., 'brand', 'product', 'campaign'
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    brand = relationship("Brand", back_populates="keywords")
