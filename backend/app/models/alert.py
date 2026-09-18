from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.models.base import Base, utc_now


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True)
    brand_id = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True)
    issue_cluster_id = Column(Integer, ForeignKey("issue_clusters.id", ondelete="CASCADE"), nullable=False, index=True)
    alert_type = Column(String(50), default="reputation_risk", nullable=False)
    severity = Column(String(50), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(50), default="open", nullable=False, index=True)
    evidence_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    email_status = Column(String(50), default="pending", nullable=False, index=True)
    email_recipients = Column(JSON, default=list, nullable=False)
    email_sent_at = Column(DateTime, nullable=True)
    email_error = Column(Text, nullable=True)
    email_severity_sent = Column(String(50), nullable=True)

    issue_cluster = relationship("IssueCluster")

    __table_args__ = (UniqueConstraint("brand_id", "issue_cluster_id", name="uq_alert_brand_cluster"),)
