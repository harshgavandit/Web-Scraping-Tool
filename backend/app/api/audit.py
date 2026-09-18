from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.post import Post
from app.models.post_analysis import PostAnalysis
from app.models.search_discovery import SearchQuery, SearchRun


router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("")
def get_audit_trail(
    brand_id: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    source_rows = (
        db.query(SearchRun, SearchQuery)
        .join(SearchQuery, SearchQuery.id == SearchRun.query_id)
        .filter(SearchQuery.brand_id == brand_id)
        .order_by(SearchRun.started_at.desc())
        .limit(limit)
        .all()
    )
    ai_rows = (
        db.query(PostAnalysis, Post)
        .join(Post, Post.id == PostAnalysis.post_id)
        .filter(Post.brand_id == brand_id)
        .order_by(PostAnalysis.analyzed_at.desc())
        .limit(limit)
        .all()
    )
    return {
        "brand_id": brand_id,
        "source_runs": [
            {
                "id": run.id,
                "provider": run.provider,
                "query": query.query,
                "category": query.category,
                "country": query.country,
                "language": query.language,
                "status": run.status,
                "results_found": run.results_found,
                "results_new": run.results_new,
                "started_at": run.started_at,
                "completed_at": run.completed_at,
                "error_message": run.error_message,
            }
            for run, query in source_rows
        ],
        "ai_analyses": [
            {
                "id": analysis.id,
                "post_id": post.id,
                "provider": analysis.analysis_provider,
                "model": analysis.model_used,
                "status": analysis.analysis_status,
                "analysis_version": analysis.analysis_version,
                "analyzed_at": analysis.analyzed_at,
                "source": post.source,
                "source_url": post.url,
                "title": post.title,
            }
            for analysis, post in ai_rows
        ],
    }
