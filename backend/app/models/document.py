from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base, utc_now


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    canonical_url = Column(Text, nullable=True)
    domain = Column(String(255), nullable=True, index=True)
    source_type = Column(String(50), default="article", nullable=False, index=True)
    content_status = Column(String(50), default="snippet_only", nullable=False, index=True)
    robots_allowed = Column(Boolean, nullable=True)
    http_status = Column(Integer, nullable=True)
    language = Column(String(20), nullable=True)
    publisher = Column(String(255), nullable=True)
    author = Column(String(255), nullable=True)
    fetched_at = Column(DateTime, default=utc_now, nullable=False)
    error_message = Column(Text, nullable=True)

    post = relationship("Post", back_populates="document")
    snapshots = relationship("DocumentSnapshot", back_populates="document", cascade="all, delete-orphan", order_by="DocumentSnapshot.created_at.desc()")


class DocumentSnapshot(Base):
    __tablename__ = "document_snapshots"

    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    content_text = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False, index=True)
    extracted_data = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    document = relationship("Document", back_populates="snapshots")
