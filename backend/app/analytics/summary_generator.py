from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from sqlalchemy import case, desc, func
from sqlalchemy.orm import Session
from app.utils.datetime_utils import utc_now

from app.models.post import Post
from app.models.post_analysis import PostAnalysis
from app.models.product_intelligence import IssueCluster, MentionEvidence
from app.schemas.dashboard import (
    DashboardKPIs, ExecutiveSummary, DashboardSummaryResponse
)
from app.analytics.trends import compute_trending_topics

# Simple memory cache keyed by (brand_id, date_range, max_post_id)
_SUMMARY_CACHE: Dict[str, Tuple[datetime, DashboardSummaryResponse]] = {}


def generate_dashboard_summary(
    db: Session,
    brand_id: int = 1,
    days: int = 30,
    force_refresh: bool = False
) -> DashboardSummaryResponse:
    """
    Computes dashboard KPIs and cached executive summary.
    Cached based on (brand_id, days, latest_post_id).
    """
    now = utc_now()
    since_date = now - timedelta(days=days)

    # Include stored-analysis freshness in the cache version. Existing posts
    # may be enriched or corrected without changing the latest post ID.
    latest_post_id = db.query(func.max(Post.id)).filter(Post.brand_id == brand_id).scalar() or 0
    latest_analysis_at = (
        db.query(func.max(PostAnalysis.analyzed_at))
        .join(Post, Post.id == PostAnalysis.post_id)
        .filter(Post.brand_id == brand_id)
        .scalar()
    )
    analysis_version = latest_analysis_at.isoformat() if latest_analysis_at else "none"
    cache_key = f"{brand_id}_{days}_{latest_post_id}_{analysis_version}"

    if not force_refresh and cache_key in _SUMMARY_CACHE:
        cached_time, cached_summary = _SUMMARY_CACHE[cache_key]
        # Keep cache for up to 15 minutes unless new post arrived
        if (now - cached_time).total_seconds() < 900:
            return cached_summary

    # Aggregate in SQL so dashboard refreshes do not materialize thousands of
    # post bodies and metadata objects in the application process.
    counts = (
        db.query(
            func.count(PostAnalysis.id),
            func.sum(case((PostAnalysis.sentiment == "Positive", 1), else_=0)),
            func.sum(case((PostAnalysis.sentiment == "Negative", 1), else_=0)),
            func.sum(case((PostAnalysis.sentiment == "Mixed", 1), else_=0)),
            func.sum(case((PostAnalysis.sentiment == "Neutral", 1), else_=0)),
            func.sum(case((PostAnalysis.is_viral.is_(True), 1), else_=0)),
        )
        .select_from(PostAnalysis)
        .join(Post, Post.id == PostAnalysis.post_id)
        .filter(Post.brand_id == brand_id)
        .filter(Post.published_at >= since_date)
        .one()
    )
    total_mentions = int(counts[0] or 0)

    if total_mentions == 0:
        # Return clean empty state
        kpis = DashboardKPIs()
        exec_summary = ExecutiveSummary(
            overall_sentiment="No data recorded for this period.",
            positive_pct=0.0,
            negative_pct=0.0,
            neutral_mixed_pct=0.0,
            top_positive_topic="N/A",
            top_negative_topic="N/A",
            fastest_growing_topic="N/A",
            most_viral_discussion="N/A",
            key_insight="Awaiting data collection to formulate insights.",
            recommended_action="Trigger a collection run to gather social chatter.",
            generated_at=now,
            data_version=f"v_{latest_post_id}"
        )
        return DashboardSummaryResponse(kpis=kpis, executive_summary=exec_summary)

    # Sentiment distribution
    pos_count = int(counts[1] or 0)
    neg_count = int(counts[2] or 0)
    mixed_count = int(counts[3] or 0)
    neu_count = int(counts[4] or 0)

    pos_pct = round((pos_count / total_mentions) * 100.0, 1)
    neg_pct = round((neg_count / total_mentions) * 100.0, 1)
    mixed_pct = round((mixed_count / total_mentions) * 100.0, 1)
    neu_pct = round((neu_count / total_mentions) * 100.0, 1)

    viral_count = int(counts[5] or 0)

    # Topic trends
    trending = compute_trending_topics(db, brand_id=brand_id, days=days)
    top_trend = trending[0].topic if trending else "General Brand"

    topic_base = (
        db.query(PostAnalysis.topic, func.count(PostAnalysis.id).label("topic_count"))
        .join(Post, Post.id == PostAnalysis.post_id)
        .filter(Post.brand_id == brand_id)
        .filter(Post.published_at >= since_date)
        .filter(PostAnalysis.topic.isnot(None))
    )
    complaint_row = (
        topic_base.filter(PostAnalysis.sentiment.in_(("Negative", "Mixed")))
        .group_by(PostAnalysis.topic)
        .order_by(desc("topic_count"), PostAnalysis.topic.asc())
        .first()
    )
    positive_row = (
        topic_base.filter(PostAnalysis.sentiment == "Positive")
        .group_by(PostAnalysis.topic)
        .order_by(desc("topic_count"), PostAnalysis.topic.asc())
        .first()
    )
    top_complaint = complaint_row[0] if complaint_row else "Pricing"
    top_positive = positive_row[0] if positive_row else "Product Comfort"

    most_viral_row = (
        db.query(Post.title, Post.source, PostAnalysis.virality_score)
        .join(PostAnalysis, Post.id == PostAnalysis.post_id)
        .filter(Post.brand_id == brand_id)
        .filter(Post.published_at >= since_date)
        .order_by(PostAnalysis.virality_score.desc(), Post.id.desc())
        .first()
    )
    most_viral_title = "N/A"
    if most_viral_row:
        title = most_viral_row.title or "Untitled discussion"
        most_viral_title = (
            f"{title}... ({most_viral_row.source.title()} - "
            f"{int(most_viral_row.virality_score or 0)} Virality)"
        )

    # Formulate Executive Summary
    dominant_sent = "predominantly positive" if pos_pct > 50 else ("largely mixed" if mixed_pct + neg_pct > 40 else "neutral to positive")
    overall_sentiment_str = f"{pos_pct}% positive, {neg_pct}% negative, {mixed_pct + neu_pct}% neutral/mixed."

    # Top risk cluster
    top_cluster = (
        db.query(IssueCluster)
        .filter(IssueCluster.brand_id == brand_id)
        .order_by(IssueCluster.risk_score.desc(), IssueCluster.mention_count.desc())
        .first()
    )
    top_risk_cluster = top_cluster.title if top_cluster else None

    # Evidence quotes from aspect evidence
    evidence_rows = (
        db.query(MentionEvidence.evidence_quote)
        .join(Post, Post.id == MentionEvidence.post_id)
        .filter(Post.brand_id == brand_id, Post.published_at >= since_date)
        .filter(MentionEvidence.sentiment.in_(("Negative", "Mixed")))
        .limit(3)
        .all()
    )
    evidence_quotes = [row[0] for row in evidence_rows if row[0]]

    # Recommendation ownership & priority
    if top_cluster and top_cluster.risk_score >= 70:
        recommendation_priority = "P0"
    elif neg_pct >= 25 or (top_cluster and top_cluster.risk_score >= 45):
        recommendation_priority = "P1"
    else:
        recommendation_priority = "P2"

    lower_complaint = top_complaint.lower()
    if any(k in lower_complaint for k in ("customer service", "delivery", "shipping", "refund", "snkrs")):
        recommendation_owner = "Customer Experience & Fulfillment"
    elif any(k in lower_complaint for k in ("pricing", "price", "expensive", "cost", "value")):
        recommendation_owner = "Product Marketing & Commercial Strategy"
    elif any(k in lower_complaint for k in ("quality", "durability", "comfort", "fit", "sole", "outsole")):
        recommendation_owner = "Product Engineering & QA"
    else:
        recommendation_owner = "Brand Communications & PR"

    # Key insight and marketing recommendation synthesis
    key_insight = (
        f"Brand sentiment remains {dominant_sent} led by {top_positive.lower()}, "
        f"while {top_complaint.lower()} represents the primary emerging headwind across social discussions."
    )

    recommended_action = (
        f"Strengthen value-for-money messaging around core performance lines while proactively "
        f"addressing community feedback regarding {top_complaint.lower()}."
    )

    kpis = DashboardKPIs(
        total_mentions=total_mentions,
        positive_pct=pos_pct,
        negative_pct=neg_pct,
        neutral_pct=neu_pct,
        mixed_pct=mixed_pct,
        viral_posts_count=viral_count,
        top_trending_topic=top_trend,
        top_complaint=top_complaint,
        top_positive_topic=top_positive
    )

    exec_summary = ExecutiveSummary(
        overall_sentiment=overall_sentiment_str,
        positive_pct=pos_pct,
        negative_pct=neg_pct,
        neutral_mixed_pct=round(mixed_pct + neu_pct, 1),
        top_positive_topic=top_positive,
        top_negative_topic=top_complaint,
        fastest_growing_topic=trending[0].topic if trending else top_trend,
        most_viral_discussion=most_viral_title,
        key_insight=key_insight,
        recommended_action=recommended_action,
        recommendation_owner=recommendation_owner,
        recommendation_priority=recommendation_priority,
        evidence_quotes=evidence_quotes,
        top_risk_cluster=top_risk_cluster,
        generated_at=now,
        data_version=f"v_{latest_post_id}"
    )

    response = DashboardSummaryResponse(kpis=kpis, executive_summary=exec_summary)
    _SUMMARY_CACHE[cache_key] = (now, response)
    return response
