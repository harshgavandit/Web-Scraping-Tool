from datetime import datetime
from typing import Literal, Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import desc, asc, or_
from sqlalchemy.orm import Session, joinedload

from app.database.session import get_db
from app.models.post import Post
from app.models.post_analysis import PostAnalysis
from app.models.document import Document
from app.models.competitor import Competitor
from app.schemas.post import PostResponse
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/posts", tags=["Posts"])


@router.get("", response_model=PaginatedResponse[PostResponse])
def get_posts(
    brand_id: Optional[int] = 1,
    source: Optional[Literal["all", "news_rss", "rss", "publisher_rss", "google_search", "web"]] = None,
    sentiment: Optional[Literal["all", "Positive", "Negative", "Neutral", "Mixed"]] = None,
    topic: Optional[str] = None,
    product: Optional[str] = None,
    competitor: Optional[str] = None,
    virality_level: Optional[Literal["all", "Low", "Medium", "High", "Viral"]] = None,
    viral: Optional[bool] = None,
    search: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    sort_by: Literal["newest", "oldest", "highest_engagement", "highest_virality", "most_negative", "most_positive"] = "newest",
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(25, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Paginated, multi-filtered list of brand posts and intelligence analysis.
    Optimized for high throughput and zero N+1 database overhead.
    """
    # Eager load analysis to eliminate N+1 queries
    query = db.query(Post).options(
        joinedload(Post.analysis),
        joinedload(Post.document).joinedload(Document.snapshots),
    ).outerjoin(PostAnalysis, Post.id == PostAnalysis.post_id)

    # 1. Filter by Brand
    if brand_id:
        query = query.filter(Post.brand_id == brand_id)

    # 2. Filter by Source
    if source and source.lower() != "all":
        query = query.filter(Post.source == source.lower())

    # 3. Filter by Sentiment
    if sentiment and sentiment.lower() != "all":
        query = query.filter(PostAnalysis.sentiment == sentiment.capitalize())

    # 4. Filter by Topic
    if topic and topic.lower() != "all":
        query = query.filter(PostAnalysis.topic.ilike(f"%{topic}%"))

    # 5. Filter by Product
    if product and product.lower() != "all":
        query = query.filter(PostAnalysis.product.ilike(f"%{product}%"))

    # 6. Filter by Competitor
    if competitor and competitor.lower() != "all":
        if competitor.lower() == "any":
            names = [row[0] for row in db.query(Competitor.name).filter(Competitor.brand_id == brand_id).all()]
            text_matches = [column.ilike(f"%{name}%") for name in names for column in (Post.title, Post.content)]
            query = query.filter(or_(
                PostAnalysis.competitor.isnot(None),
                PostAnalysis.competitor != "",
                *text_matches,
            ))
        else:
            competitor_term = f"%{competitor.strip()}%"
            query = query.filter(or_(
                PostAnalysis.competitor.ilike(competitor_term),
                Post.title.ilike(competitor_term),
                Post.content.ilike(competitor_term),
            ))

    # 7. Filter by Virality Level
    if virality_level and virality_level.lower() != "all":
        query = query.filter(PostAnalysis.virality_level == virality_level.capitalize())

    # 8. Viral Only Toggle
    if viral is True:
        query = query.filter(or_(
            PostAnalysis.is_viral.is_(True),
            PostAnalysis.attention_score >= 40,
        ))

    # 9. Date Range Filtering
    if date_from:
        query = query.filter(Post.published_at >= date_from)
    if date_to:
        query = query.filter(Post.published_at <= date_to)

    # 10. Free Text Search (matches title, content, topic, product, competitor)
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Post.title.ilike(term),
                Post.content.ilike(term),
                PostAnalysis.topic.ilike(term),
                PostAnalysis.product.ilike(term),
                PostAnalysis.competitor.ilike(term),
            )
        )

    total = query.order_by(None).count()

    # 11. Sorting
    if sort_by == "oldest":
        query = query.order_by(asc(Post.published_at))
    elif sort_by == "highest_engagement":
        query = query.order_by(desc(Post.engagement_count))
    elif sort_by == "highest_virality":
        query = query.order_by(
            desc(PostAnalysis.attention_score),
            desc(PostAnalysis.virality_score),
            desc(Post.published_at),
        )
    elif sort_by == "most_negative":
        # Sort negative sentiment posts first, lowest sentiment score
        query = query.order_by(asc(PostAnalysis.sentiment_score))
    elif sort_by == "most_positive":
        query = query.order_by(desc(PostAnalysis.sentiment_score))
    else:  # newest / default (high virality + newest)
        query = query.order_by(desc(Post.published_at))

    pages = (total + page_size - 1) // page_size if total > 0 else 1

    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return PaginatedResponse[PostResponse](
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        pages=pages
    )


@router.get("/viral", response_model=List[PostResponse])
def get_viral_posts(
    brand_id: Optional[int] = 1,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Retrieve top viral discussions for the brand."""
    query = (
        db.query(Post)
        .options(joinedload(Post.analysis), joinedload(Post.document).joinedload(Document.snapshots))
        .join(PostAnalysis, Post.id == PostAnalysis.post_id)
        .filter(Post.brand_id == brand_id)
        .filter(PostAnalysis.is_viral.is_(True))
        .order_by(desc(PostAnalysis.virality_score))
        .limit(limit)
    )
    return query.all()


@router.get("/{post_id}", response_model=PostResponse)
def get_post_detail(post_id: int, db: Session = Depends(get_db)):
    """Retrieve complete details and AI analysis for a specific post."""
    post = (
        db.query(Post)
        .options(joinedload(Post.analysis), joinedload(Post.document).joinedload(Document.snapshots))
        .filter(Post.id == post_id)
        .first()
    )
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post
