from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from app.database.session import get_db
from app.models.post import Post
from app.models.post_analysis import PostAnalysis
from app.models.tracked_keyword import TrackedKeyword
from app.services.ai_service import ai_service
from app.services.sentiment_service import analyze_local_sentiment
from app.core.config import settings
from app.utils.datetime_utils import utc_now
from app.services.product_intelligence_service import persist_post_intelligence, rebuild_issue_clusters
from app.services.alert_service import dispatch_email_alerts, sync_reputation_alerts
from app.services.gemini_service import GeminiError
from app.models.document import Document

router = APIRouter(prefix="/analysis", tags=["Analysis"])


def _gemini_payload(post: Post) -> dict:
    local_label, local_score, _ = analyze_local_sentiment(f"{post.title or ''} {post.content}")
    return {
        "id": post.id, "title": post.title, "content": post.content,
        "source_url": post.url, "local_sentiment": local_label,
        "sentiment_score": local_score,
    }


def _analysis_record(db: Session, post: Post) -> PostAnalysis:
    analysis = db.query(PostAnalysis).filter(PostAnalysis.post_id == post.id).first()
    if analysis is None:
        label, score, _ = analyze_local_sentiment(f"{post.title or ''} {post.content}")
        analysis = PostAnalysis(post_id=post.id, sentiment=label, sentiment_score=score)
        db.add(analysis)
    return analysis


def _mark_gemini_failed(db: Session, post: Post) -> None:
    analysis = _analysis_record(db, post)
    for field in ("topic", "product", "competitor", "key_positive", "key_negative", "summary", "recommendation"):
        setattr(analysis, field, None)
    analysis.analysis_provider = "gemini"
    analysis.analysis_status = "failed"
    analysis.model_used = settings.GEMINI_MODEL
    analysis.analyzed_at = utc_now()


def _persist_gemini_result(db: Session, post: Post, item) -> PostAnalysis:
    analysis = _analysis_record(db, post)
    label, score, _ = analyze_local_sentiment(f"{post.title or ''} {post.content}")
    # Keep dashboard sentiment measurements deterministic and comparable across
    # collection runs; Gemini enriches the context and recommended response.
    analysis.sentiment = label
    analysis.sentiment_score = score
    for field in ("topic", "product", "competitor", "key_positive", "key_negative", "summary", "recommendation"):
        setattr(analysis, field, getattr(item, field))
    analysis.analysis_provider = "gemini"
    analysis.analysis_status = "completed"
    analysis.model_used = settings.GEMINI_MODEL
    analysis.analyzed_at = utc_now()
    return analysis


@router.post("/posts/{post_id}/refresh")
def refresh_post_analysis(post_id: int, db: Session = Depends(get_db)):
    """Run a fresh, single-article Gemini analysis and persist its real result."""
    post = db.query(Post).filter(Post.id == post_id).first()
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    try:
        results = ai_service.analyze_batch([_gemini_payload(post)])
        if len(results) != 1 or results[0].post_id != post.id:
            raise GeminiError("Gemini did not return the requested article analysis.")
        analysis = _persist_gemini_result(db, post, results[0])
        products = [row[0] for row in db.query(TrackedKeyword.keyword).filter(
            TrackedKeyword.brand_id == post.brand_id,
            TrackedKeyword.category == "product",
            TrackedKeyword.active.is_(True),
        ).all()]
        db.flush()
        persist_post_intelligence(db, post, analysis, products)
        rebuild_issue_clusters(db, brand_id=post.brand_id)
        db.commit()
    except GeminiError as exc:
        db.rollback()
        post = db.query(Post).filter(Post.id == post_id).first()
        _mark_gemini_failed(db, post)
        db.commit()
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return db.query(Post).options(
        joinedload(Post.analysis), joinedload(Post.document).joinedload(Document.snapshots)
    ).filter(Post.id == post_id).first()


@router.post("/run")
def trigger_analysis(
    brand_id: int = Query(1, description="Brand ID to analyze"),
    force_all: bool = Query(False, description="Re-analyze existing posts"),
    limit: int = Query(50, ge=1, le=200, description="Max posts to analyze"),
    db: Session = Depends(get_db)
):
    """
    Trigger batch AI analysis on unanalyzed (or all) posts for the brand.
    """
    query = db.query(Post).filter(Post.brand_id == brand_id)
    if not force_all:
        query = query.outerjoin(PostAnalysis, Post.id == PostAnalysis.post_id).filter(PostAnalysis.id.is_(None))

    posts = query.limit(limit).all()
    if not posts:
        return {"message": "No unanalyzed posts found for this brand.", "analyzed": 0}

    batch_payload = [_gemini_payload(post) for post in posts]

    results = []
    batch_size = max(1, settings.AI_BATCH_SIZE or 20)
    try:
        for index in range(0, len(batch_payload), batch_size):
            results.extend(ai_service.analyze_batch(batch_payload[index:index + batch_size]))
    except GeminiError as exc:
        db.rollback()
        posts = db.query(Post).filter(Post.id.in_([item["id"] for item in batch_payload])).all()
        for post in posts:
            _mark_gemini_failed(db, post)
        db.commit()
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    results_map = {r.post_id: r for r in results}

    product_names = [row[0] for row in db.query(TrackedKeyword.keyword).filter(
        TrackedKeyword.brand_id == brand_id,
        TrackedKeyword.category == "product",
        TrackedKeyword.active.is_(True),
    ).all()]
    updated_count = 0
    for p in posts:
        item = results_map.get(p.id)
        if not item:
            continue

        existing_analysis = _persist_gemini_result(db, p, item)
        db.flush()
        persist_post_intelligence(db, p, existing_analysis, product_names)
        updated_count += 1

    rebuild_issue_clusters(db, brand_id=brand_id)
    alerts = sync_reputation_alerts(db, brand_id=brand_id)
    dispatch_email_alerts(db, alerts)
    db.commit()
    return {"message": f"Successfully analyzed {updated_count} posts.", "analyzed": updated_count}
