import hashlib
import re
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
from typing import Optional
from sqlalchemy.orm import Session
from app.models.post import Post

# Common tracking parameters to strip for canonical URL
TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "msclkid", "ref", "ref_src", "igshid", "mc_cid", "mc_eid"
}


def normalize_text(text: str) -> str:
    """Normalize text for consistent duplicate detection."""
    if not text:
        return ""
    # Lowercase
    cleaned = text.lower()
    # Replace multiple whitespace/newlines with single space
    cleaned = re.sub(r"\s+", " ", cleaned)
    # Strip leading and trailing whitespace
    return cleaned.strip()


def compute_content_hash(text: str) -> str:
    """Generate a SHA-256 hash for normalized content."""
    normalized = normalize_text(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def canonicalize_url(url: Optional[str]) -> Optional[str]:
    """Strip marketing tracking parameters and normalize URL structure."""
    if not url:
        return None
    try:
        parsed = urlparse(url.strip())
        if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
            return None

        # Filter out tracking query params
        query_pairs = parse_qsl(parsed.query, keep_blank_values=False)
        filtered_query = [(k, v) for k, v in query_pairs if k.lower() not in TRACKING_PARAMS]
        clean_query = urlencode(sorted(filtered_query))

        clean_path = parsed.path.rstrip("/")
        if not clean_path:
            clean_path = "/"

        canonical = urlunparse((
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            clean_path,
            parsed.params,
            clean_query,
            ""  # drop fragment
        ))
        return canonical
    except Exception:
        return url.strip()


def is_duplicate_post(
    db: Session,
    source: str,
    external_id: Optional[str],
    content_hash: str,
    url: Optional[str] = None
) -> bool:
    """
    Check if a post is already recorded using 3-layer deduplication:
    1. Source + external ID
    2. Exact content_hash
    3. Canonical URL
    """
    # 1. External ID check
    if external_id:
        existing = db.query(Post.id).filter(
            Post.source == source,
            Post.external_id == external_id
        ).first()
        if existing:
            return True

    # 2. Content hash check
    existing_hash = db.query(Post.id).filter(
        Post.content_hash == content_hash
    ).first()
    if existing_hash:
        return True

    # 3. Canonical URL check
    if url:
        canonical = canonicalize_url(url)
        if canonical:
            existing_url = db.query(Post.id).filter(
                Post.url == canonical
            ).first()
            if existing_url:
                return True

    return False
