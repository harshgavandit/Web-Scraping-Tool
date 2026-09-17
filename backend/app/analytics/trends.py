from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.post import Post
from app.models.post_analysis import PostAnalysis
from app.schemas.dashboard import TopicTrendItem


from app.utils.datetime_utils import utc_now


def compute_trending_topics(db: Session, brand_id: int = 1, days: int = 7) -> List[TopicTrendItem]:
    """
    Calculate trending topics by comparing current period with previous period.
    Tracks: current count, previous count, percentage change, sentiment, avg virality, and trend direction.
    """
    now = utc_now()
    current_start = now - timedelta(days=days)
    previous_start = current_start - timedelta(days=days)

    # 1. Current window topic aggregates
    current_q = (
        db.query(
            PostAnalysis.topic,
            func.count(Post.id).label("count"),
            func.avg(PostAnalysis.virality_score).label("avg_virality"),
            func.avg(PostAnalysis.sentiment_score).label("avg_sentiment_score"),
        )
        .join(Post, Post.id == PostAnalysis.post_id)
        .filter(Post.brand_id == brand_id)
        .filter(Post.published_at >= current_start)
        .filter(PostAnalysis.topic.isnot(None))
        .group_by(PostAnalysis.topic)
        .all()
    )

    # 2. Previous window topic counts
    previous_q = (
        db.query(
            PostAnalysis.topic,
            func.count(Post.id).label("count")
        )
        .join(Post, Post.id == PostAnalysis.post_id)
        .filter(Post.brand_id == brand_id)
        .filter(Post.published_at >= previous_start)
        .filter(Post.published_at < current_start)
        .filter(PostAnalysis.topic.isnot(None))
        .group_by(PostAnalysis.topic)
        .all()
    )

    prev_counts = {item[0]: item[1] for item in previous_q}

    trend_items: List[TopicTrendItem] = []
    for topic, cur_count, avg_virality, avg_sent in current_q:
        prev_count = prev_counts.get(topic, 0)
        if prev_count > 0:
            pct_change = round(((cur_count - prev_count) / prev_count) * 100.0, 1)
        else:
            pct_change = 100.0 if cur_count > 0 else 0.0

        if pct_change >= 20.0:
            direction = "Rising"
        elif pct_change <= -20.0:
            direction = "Falling"
        else:
            direction = "Steady"

        # Sentiment representation
        sent_label = "Neutral"
        if avg_sent is not None:
            if avg_sent >= 0.15:
                sent_label = "Positive"
            elif avg_sent <= -0.15:
                sent_label = "Negative"
            elif abs(avg_sent) < 0.15 and cur_count > 1:
                sent_label = "Mixed"

        trend_items.append(
            TopicTrendItem(
                topic=topic,
                current_count=cur_count,
                previous_count=prev_count,
                pct_change=pct_change,
                sentiment=sent_label,
                avg_virality=round(avg_virality or 0.0, 1),
                trend_direction=direction
            )
        )

    # Sort primarily by current volume & virality
    trend_items.sort(key=lambda x: (x.current_count, x.avg_virality), reverse=True)
    return trend_items
