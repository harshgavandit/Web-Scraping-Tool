from collections import defaultdict
from datetime import timedelta
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.intelligence.product_intelligence import (
    calculate_attention_score,
    calculate_reputation_risk,
    extract_aspect_evidence,
    resolve_product,
)
from app.models.post import Post
from app.models.post_analysis import PostAnalysis
from app.models.product_intelligence import IssueCluster, MentionEvidence, Product
from app.utils.datetime_utils import utc_now


def _sync_products(db: Session, brand_id: int, product_names: list[str]) -> list[Product]:
    products = db.query(Product).filter(Product.brand_id == brand_id).all()
    existing = {product.name.casefold(): product for product in products}
    for name in dict.fromkeys(value.strip() for value in product_names if value and value.strip()):
        if name.casefold() not in existing:
            product = Product(brand_id=brand_id, name=name, aliases=[name])
            db.add(product)
            db.flush()
            products.append(product)
            existing[name.casefold()] = product
    return products


def persist_post_intelligence(
    db: Session,
    post: Post,
    analysis: PostAnalysis,
    product_names: list[str],
) -> None:
    products = _sync_products(db, post.brand_id, product_names)
    candidates = [{"name": product.name, "aliases": product.aliases or []} for product in products]
    resolved_name = resolve_product(f"{post.title or ''} {post.content}", candidates) or analysis.product
    product = next((item for item in products if item.name.casefold() == (resolved_name or "").casefold()), None)
    if product:
        analysis.product = product.name

    db.query(MentionEvidence).filter(MentionEvidence.post_id == post.id).delete(synchronize_session=False)
    for item in extract_aspect_evidence(post.content):
        db.add(MentionEvidence(
            post_id=post.id,
            product_id=product.id if product else None,
            aspect=item.aspect,
            sentiment=item.sentiment,
            sentiment_score=item.score,
            evidence_quote=item.quote,
            confidence=item.confidence,
        ))

    metadata = post.raw_metadata or {}
    product_data = (metadata.get("page_fetch") or {}).get("product_data") or {}
    attention_score, attention_level, attention_reasons = calculate_attention_score(
        published_at=post.published_at,
        search_position=metadata.get("search_position"),
        review_count=product_data.get("review_count"),
    )
    analysis.attention_score = attention_score
    analysis.attention_level = attention_level
    analysis.attention_reasons = attention_reasons
    if not metadata.get("engagement_available", False):
        analysis.virality_score = 0.0
        analysis.virality_level = "Low"
        analysis.is_viral = False
    db.flush()


def rebuild_issue_clusters(db: Session, brand_id: int, days: int = 30) -> None:
    now = utc_now()
    current_start = now - timedelta(days=days)
    previous_start = current_start - timedelta(days=days)
    rows = (
        db.query(MentionEvidence, Post, PostAnalysis, Product)
        .join(Post, Post.id == MentionEvidence.post_id)
        .join(PostAnalysis, PostAnalysis.post_id == Post.id)
        .outerjoin(Product, Product.id == MentionEvidence.product_id)
        .filter(Post.brand_id == brand_id)
        .filter(Post.published_at >= previous_start)
        .filter(MentionEvidence.sentiment.in_(("Negative", "Mixed")))
        .all()
    )
    groups = defaultdict(list)
    for evidence, post, analysis, product in rows:
        groups[(product.id if product else None, evidence.aspect)].append((evidence, post, analysis, product))

    db.query(IssueCluster).filter(IssueCluster.brand_id == brand_id).delete(synchronize_session=False)
    for (product_id, aspect), items in groups.items():
        current = [item for item in items if item[1].published_at and item[1].published_at >= current_start]
        if not current:
            continue
        previous_count = len(items) - len(current)
        growth = round(((len(current) - previous_count) / previous_count) * 100.0, 1) if previous_count else 100.0
        sources = {
            (item[1].raw_metadata or {}).get("display_domain")
            or urlparse(item[1].url or "").netloc
            or item[1].source
            for item in current
        }
        confidence = sum(item[0].confidence for item in current) / len(current)
        risk_score, risk_level = calculate_reputation_risk(len(current), len(sources), growth, confidence)
        product = current[0][3]
        db.add(IssueCluster(
            brand_id=brand_id,
            product_id=product_id,
            title=f"{product.name if product else 'Brand'} {aspect.lower()} concerns",
            aspect=aspect,
            sentiment="Negative",
            mention_count=len(current),
            unique_sources=len(sources),
            growth_pct=growth,
            attention_score=round(sum(item[2].attention_score for item in current) / len(current), 1),
            risk_score=risk_score,
            risk_level=risk_level,
            confidence=round(confidence, 2),
            first_seen_at=min(item[1].published_at for item in current),
            last_seen_at=max(item[1].published_at for item in current),
            updated_at=now,
        ))
    db.flush()
