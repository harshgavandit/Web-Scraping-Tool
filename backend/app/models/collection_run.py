from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from app.models.base import Base, utc_now


class CollectionRun(Base):
    __tablename__ = "collection_runs"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(100), nullable=False, index=True)
    started_at = Column(DateTime, default=utc_now, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    records_found = Column(Integer, default=0, nullable=False)
    records_added = Column(Integer, default=0, nullable=False)
    records_skipped = Column(Integer, default=0, nullable=False)
    status = Column(String(50), default="running", nullable=False)  # running, completed, failed
    error_message = Column(Text, nullable=True)
