from collections import defaultdict
from datetime import datetime
from typing import Iterable, Sequence
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.collectors.base import RawPost
from app.discovery.query_planner import GoogleQuerySpec
from app.models.search_discovery import SearchQuery, SearchResult, SearchRun
from app.utils.datetime_utils import utc_now


def record_discovery_audit(
    db: Session,
    brand_id: int,
    provider: str,
    specs: Sequence[GoogleQuerySpec],
    raw_posts: Iterable[RawPost],
    started_at: datetime,
    status: str = "completed",
    error_message: str | None = None,
) -> None:
    """Persist query coverage and result provenance independently of post enrichment."""
    posts_by_query = defaultdict(list)
    for post in raw_posts:
        query_text = (post.raw_metadata or {}).get("google_query")
        if query_text:
            posts_by_query[query_text].append(post)

    completed_at = utc_now()
    for spec in specs:
        query_record = db.query(SearchQuery).filter_by(
            brand_id=brand_id,
            provider=provider,
            query=spec.query,
            country="US",
            language="en",
        ).first()
        if query_record is None:
            query_record = SearchQuery(
                brand_id=brand_id,
                provider=provider,
                query=spec.query,
                category=spec.category,
                product=spec.product,
                competitor=spec.competitor,
                country="US",
                language="en",
            )
            db.add(query_record)
            db.flush()
        query_record.last_run_at = completed_at

        matching_posts = posts_by_query.get(spec.query, [])
        search_run = SearchRun(
            query_id=query_record.id,
            provider=provider,
            started_at=started_at,
            completed_at=completed_at,
            status=status,
            results_found=len(matching_posts),
            results_new=0,
            error_message=error_message,
        )
        db.add(search_run)
        db.flush()

        for post in matching_posts:
            existing = db.query(SearchResult).filter_by(
                query_id=query_record.id,
                url=post.url,
            ).first()
            if existing:
                existing.last_seen_at = completed_at
                existing.position = post.raw_metadata.get("search_position")
                existing.search_run_id = search_run.id
                continue
            domain = post.raw_metadata.get("display_domain") or urlparse(post.url or "").netloc
            db.add(SearchResult(
                query_id=query_record.id,
                search_run_id=search_run.id,
                provider=provider,
                title=post.title,
                snippet=post.content,
                url=post.url,
                display_domain=domain,
                position=post.raw_metadata.get("search_position"),
                published_at=post.published_at,
                country=post.raw_metadata.get("country") or "US",
                language=post.raw_metadata.get("language") or "en",
                raw_metadata=post.raw_metadata,
            ))
            search_run.results_new += 1

    db.commit()
