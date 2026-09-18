import csv
import io
from collections import Counter, defaultdict
from datetime import timedelta

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session, joinedload

from app.database.session import get_db
from app.models.post import Post
from app.models.post_analysis import PostAnalysis
from app.models.product_intelligence import IssueCluster, MentionEvidence, Product
from app.models.tracked_keyword import TrackedKeyword
from app.schemas.intelligence import (
    CompetitorInsight,
    IntelligenceOverview,
    PraiseInsight,
    ProductInsight,
    RiskInsight,
)
from app.utils.datetime_utils import utc_now
from app.services.pdf_export_service import build_simple_pdf
from app.services.product_intelligence_service import persist_post_intelligence, rebuild_issue_clusters
from app.services.alert_service import dispatch_email_alerts, sync_reputation_alerts


router = APIRouter(prefix="/intelligence", tags=["Intelligence"])


@router.post("/rebuild")
def rebuild_brand_intelligence(
    brand_id: int = Query(1, ge=1),
    db: Session = Depends(get_db),
):
    product_names = [row[0] for row in db.query(TrackedKeyword.keyword).filter(
        TrackedKeyword.brand_id == brand_id,
        TrackedKeyword.category == "product",
        TrackedKeyword.active.is_(True),
    ).all()]
    posts = (
        db.query(Post)
        .options(joinedload(Post.analysis))
        .filter(Post.brand_id == brand_id)
        .all()
    )
    processed = 0
    for post in posts:
        if post.analysis is None:
            continue
        persist_post_intelligence(db, post, post.analysis, product_names)
        processed += 1
    rebuild_issue_clusters(db, brand_id=brand_id)
    alerts = sync_reputation_alerts(db, brand_id=brand_id)
    emails_sent = dispatch_email_alerts(db, alerts)
    db.commit()
    return {
        "brand_id": brand_id,
        "posts_processed": processed,
        "evidence_count": db.query(MentionEvidence).join(Post, Post.id == MentionEvidence.post_id).filter(Post.brand_id == brand_id).count(),
        "risk_count": db.query(IssueCluster).filter(IssueCluster.brand_id == brand_id).count(),
        "emails_sent": emails_sent,
    }


@router.get("/export.csv")
def export_intelligence_csv(
    brand_id: int = Query(1, ge=1),
    db: Session = Depends(get_db),
):
    clusters = (
        db.query(IssueCluster)
        .filter(IssueCluster.brand_id == brand_id)
        .order_by(IssueCluster.risk_score.desc(), IssueCluster.mention_count.desc())
        .all()
    )
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "cluster_id", "product", "aspect", "title", "sentiment", "mention_count",
        "independent_sources", "growth_pct", "attention_score", "risk_score",
        "risk_level", "confidence", "first_seen_at", "last_seen_at",
    ])
    for cluster in clusters:
        writer.writerow([
            cluster.id, cluster.product.name if cluster.product else "", cluster.aspect,
            cluster.title, cluster.sentiment, cluster.mention_count, cluster.unique_sources,
            cluster.growth_pct, cluster.attention_score, cluster.risk_score, cluster.risk_level,
            cluster.confidence,
            cluster.first_seen_at.isoformat() if cluster.first_seen_at else "",
            cluster.last_seen_at.isoformat() if cluster.last_seen_at else "",
        ])
    return Response(
        content=output.getvalue(), media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="brand_{brand_id}_intelligence.csv"'},
    )


@router.get("/export.pdf")
def export_intelligence_pdf(
    brand_id: int = Query(1, ge=1),
    db: Session = Depends(get_db),
):
    clusters = (
        db.query(IssueCluster)
        .filter(IssueCluster.brand_id == brand_id)
        .order_by(IssueCluster.risk_score.desc(), IssueCluster.mention_count.desc())
        .all()
    )
    lines = ["Evidence-backed reputation risks", ""]
    if not clusters:
        lines.append("No reputation risks were detected for this brand.")
    for cluster in clusters:
        product = cluster.product.name if cluster.product else "Brand-wide"
        lines.extend([
            f"{cluster.risk_level}: {cluster.title}",
            f"Product: {product} | Aspect: {cluster.aspect}",
            f"Evidence: {cluster.mention_count} mentions across {cluster.unique_sources} independent sources",
            f"Growth: {cluster.growth_pct:.0f}% | Attention: {cluster.attention_score:.0f}/100 | Risk: {cluster.risk_score:.0f}/100",
            "",
        ])
    payload = build_simple_pdf(f"Brand {brand_id} Intelligence Report", lines)
    return Response(
        content=payload,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="brand_{brand_id}_intelligence.pdf"'},
    )
@router.get("/overview", response_model=IntelligenceOverview)
def get_intelligence_overview(
    brand_id: int = Query(1, ge=1),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    since = utc_now() - timedelta(days=days)
    rows = (
        db.query(Product, MentionEvidence, PostAnalysis)
        .join(MentionEvidence, MentionEvidence.product_id == Product.id)
        .join(Post, Post.id == MentionEvidence.post_id)
        .join(PostAnalysis, PostAnalysis.post_id == Post.id)
        .filter(Product.brand_id == brand_id, Post.published_at >= since)
        .all()
    )
    grouped = defaultdict(list)
    for product, evidence, analysis in rows:
        grouped[product.name].append((evidence, analysis))
    products = []
    for name, items in grouped.items():
        positive = Counter(item[0].aspect for item in items if item[0].sentiment == "Positive")
        negative = Counter(item[0].aspect for item in items if item[0].sentiment in {"Negative", "Mixed"})
        products.append(ProductInsight(
            product=name,
            mention_count=len({item[0].post_id for item in items}),
            positive_count=sum(positive.values()),
            negative_count=sum(negative.values()),
            top_praise=positive.most_common(1)[0][0] if positive else None,
            top_complaint=negative.most_common(1)[0][0] if negative else None,
            average_attention=round(sum(item[1].attention_score for item in items) / len(items), 1),
        ))
    products.sort(key=lambda item: (item.mention_count, item.average_attention), reverse=True)

    clusters = (
        db.query(IssueCluster)
        .filter(IssueCluster.brand_id == brand_id)
        .order_by(IssueCluster.risk_score.desc(), IssueCluster.mention_count.desc())
        .limit(20)
        .all()
    )
    risks = [RiskInsight(
        id=cluster.id,
        title=cluster.title,
        product=cluster.product.name if cluster.product else None,
        aspect=cluster.aspect,
        mention_count=cluster.mention_count,
        unique_sources=cluster.unique_sources,
        growth_pct=cluster.growth_pct,
        attention_score=cluster.attention_score,
        risk_score=cluster.risk_score,
        risk_level=cluster.risk_level,
        confidence=cluster.confidence,
        last_seen_at=cluster.last_seen_at,
    ) for cluster in clusters]

    praise_groups = defaultdict(list)
    for product, evidence, analysis in rows:
        if evidence.sentiment == "Positive":
            praise_groups[(product.name, evidence.aspect)].append((evidence, analysis))

    praises = []
    for (prod_name, aspect), items in praise_groups.items():
        best_quote = max(items, key=lambda x: len(x[0].evidence_quote or ""))[0].evidence_quote
        avg_att = round(sum(x[1].attention_score for x in items) / len(items), 1)
        praises.append(PraiseInsight(
            product=prod_name,
            aspect=aspect,
            mention_count=len(items),
            top_quote=best_quote,
            average_attention=avg_att,
        ))
    praises.sort(key=lambda x: (x.mention_count, x.average_attention), reverse=True)

    competitor_rows = (
        db.query(PostAnalysis)
        .join(Post, Post.id == PostAnalysis.post_id)
        .filter(
            Post.brand_id == brand_id,
            Post.published_at >= since,
            PostAnalysis.competitor.isnot(None),
            PostAnalysis.competitor != "",
        )
        .all()
    )
    comp_groups = defaultdict(list)
    for analysis in competitor_rows:
        comp_groups[analysis.competitor].append(analysis)

    competitors = []
    for comp_name, items in comp_groups.items():
        pos_cnt = sum(1 for a in items if a.sentiment == "Positive")
        neg_cnt = sum(1 for a in items if a.sentiment in ("Negative", "Mixed"))
        neu_cnt = sum(1 for a in items if a.sentiment == "Neutral")
        top_topics = [t for t, _ in Counter(a.topic for a in items if a.topic).most_common(3)]
        avg_att = round(sum(a.attention_score for a in items) / len(items), 1)
        competitors.append(CompetitorInsight(
            competitor=comp_name,
            mention_count=len(items),
            positive_count=pos_cnt,
            negative_count=neg_cnt,
            neutral_count=neu_cnt,
            top_topics=top_topics,
            average_attention=avg_att,
        ))
    competitors.sort(key=lambda c: c.mention_count, reverse=True)

    return IntelligenceOverview(
        products=products,
        risks=risks,
        praises=praises,
        competitors=competitors,
    )
