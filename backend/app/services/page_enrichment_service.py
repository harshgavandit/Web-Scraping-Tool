import hashlib
from typing import Iterable, List
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.collectors.base import RawPost
from app.core.config import settings
from app.models.document import Document, DocumentSnapshot
from app.models.post import Post
from app.services.page_fetch_service import page_fetch_service
from app.utils.datetime_utils import utc_now


def enrich_raw_posts(raw_posts: Iterable[RawPost]) -> List[RawPost]:
    posts = list(raw_posts)
    if not settings.PAGE_FETCH_ENABLED:
        return posts

    for post in posts[:settings.PAGE_FETCH_LIMIT_PER_RUN]:
        if not post.url:
            continue
        result = page_fetch_service.fetch(post.url)
        metadata = dict(post.raw_metadata or {})
        metadata["page_fetch"] = {
            "status": result.status,
            "requested_url": result.requested_url,
            "final_url": result.final_url,
            "robots_allowed": result.robots_allowed,
            "http_status": result.http_status,
            "error": result.error,
            "fetched_at": utc_now().isoformat(),
        }
        if result.document:
            document = result.document
            if document.main_text.strip():
                post.content = document.main_text.strip()
            post.title = document.title or post.title
            post.author = document.author or document.publisher or post.author
            post.published_at = post.published_at or document.published_at
            post.url = document.canonical_url or result.final_url or post.url
            metadata["page_fetch"].update({
                "canonical_url": document.canonical_url,
                "publisher": document.publisher,
                "author": document.author,
                "source_type": document.source_type,
                "language": document.language,
                "product_data": document.product_data,
                "structured_data": document.structured_data,
            })
        post.raw_metadata = metadata
    return posts


def persist_document_snapshot(db: Session, post: Post) -> None:
    fetch = (post.raw_metadata or {}).get("page_fetch")
    if not fetch:
        return
    document = db.query(Document).filter_by(post_id=post.id).first()
    if document is None:
        document = Document(post_id=post.id)
        db.add(document)
        db.flush()
    canonical_url = fetch.get("canonical_url") or post.url
    document.canonical_url = canonical_url
    document.domain = urlparse(canonical_url or "").netloc or None
    document.source_type = fetch.get("source_type") or "article"
    document.content_status = fetch.get("status") or "failed"
    document.robots_allowed = fetch.get("robots_allowed")
    document.http_status = fetch.get("http_status")
    document.language = fetch.get("language")
    document.publisher = fetch.get("publisher")
    document.author = fetch.get("author")
    document.error_message = fetch.get("error")
    document.fetched_at = utc_now()

    content_hash = hashlib.sha256(post.content.encode("utf-8")).hexdigest()
    existing = db.query(DocumentSnapshot).filter_by(
        document_id=document.id,
        content_hash=content_hash,
    ).first()
    if existing is None:
        db.add(DocumentSnapshot(
            document_id=document.id,
            content_text=post.content,
            content_hash=content_hash,
            extracted_data={
                "product_data": fetch.get("product_data") or {},
                "structured_data": fetch.get("structured_data") or [],
            },
        ))
