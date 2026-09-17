from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.post import Post
from app.models.post_analysis import PostAnalysis
from app.services.ai_service import ai_service
from app.services.sentiment_service import analyze_local_sentiment
from app.core.config import settings
from app.utils.datetime_utils import utc_now

router = APIRouter(prefix="/analysis", tags=["Analysis"])


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

    batch_payload = []
    for p in posts:
        s_label, s_score, _ = analyze_local_sentiment(f"{p.title or ''} {p.content}")
        batch_payload.append({
            "id": p.id,
            "title": p.title,
            "content": p.content,
            "local_sentiment": s_label,
            "sentiment_score": s_score
        })

    results = []
    batch_size = max(1, settings.AI_BATCH_SIZE or 20)
    for index in range(0, len(batch_payload), batch_size):
        results.extend(ai_service.analyze_batch(batch_payload[index:index + batch_size]))
    results_map = {r.post_id: r for r in results}

    updated_count = 0
    for p in posts:
        item = results_map.get(p.id)
        if not item:
            continue

        existing_analysis = db.query(PostAnalysis).filter(PostAnalysis.post_id == p.id).first()
        if not existing_analysis:
            existing_analysis = PostAnalysis(post_id=p.id)
            db.add(existing_analysis)

        local_label, local_score, _ = analyze_local_sentiment(f"{p.title or ''} {p.content}")
        existing_analysis.sentiment = local_label
        existing_analysis.sentiment_score = local_score
        existing_analysis.topic = item.topic
        existing_analysis.product = item.product
        existing_analysis.competitor = item.competitor
        existing_analysis.key_positive = item.key_positive
        existing_analysis.key_negative = item.key_negative
        existing_analysis.summary = item.summary
        existing_analysis.recommendation = item.recommendation
        existing_analysis.model_used = ai_service.active_model_name
        existing_analysis.analyzed_at = utc_now()
        updated_count += 1

    db.commit()
    return {"message": f"Successfully analyzed {updated_count} posts.", "analyzed": updated_count}
