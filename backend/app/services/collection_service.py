from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from app.utils.datetime_utils import utc_now

from app.core.logging import logger
from app.core.config import settings
from app.models.brand import Brand
from app.models.post import Post
from app.models.post_analysis import PostAnalysis
from app.models.collection_run import CollectionRun

from app.collectors import get_collectors
from app.services.deduplication_service import compute_content_hash, canonicalize_url, is_duplicate_post
from app.services.relevance_service import evaluate_relevance
from app.services.sentiment_service import analyze_local_sentiment
from app.services.virality_service import calculate_engagement_and_virality
from app.services.ai_service import ai_service
from app.services.gemini_service import GeminiError
from app.services.discovery_audit_service import record_discovery_audit
from app.services.page_enrichment_service import enrich_raw_posts, persist_document_snapshot
from app.services.product_intelligence_service import persist_post_intelligence, rebuild_issue_clusters
from app.services.alert_service import dispatch_email_alerts, sync_reputation_alerts


class CollectionService:
    @staticmethod
    def run_pipeline(db: Session, brand_id: int = 1, source: str = "all", limit_per_source: int = 30) -> List[CollectionRun]:
        """
        Executes the cheap processing pipeline end-to-end:
        COLLECT -> NORMALIZE -> DEDUPLICATE -> RELEVANCE FILTER ->
        LOCAL SIGNALS -> ENGAGEMENT & VIRALITY -> BATCH GEMINI -> DATABASE
        """
        brand = db.query(Brand).filter(Brand.id == brand_id).first()
        if not brand:
            logger.error(f"Brand ID {brand_id} not found.")
            return []

        brand_name = brand.name
        keywords = [k.keyword for k in brand.keywords if k.active] or [brand_name]
        competitors = [c.name for c in brand.competitors] or ["Adidas", "Puma", "New Balance"]
        product_names = [k.keyword for k in brand.keywords if k.category == "product"] or ["Pegasus", "Air Max", "Air Jordan"]

        collectors = get_collectors(source)
        run_records: List[CollectionRun] = []

        for collector in collectors:
            query_specs = (
                collector.build_queries(brand_name, keywords, competitors)
                if hasattr(collector, "build_queries")
                else []
            )
            run_rec = CollectionRun(
                source=collector.source_name,
                started_at=utc_now(),
                status="running"
            )
            db.add(run_rec)
            db.commit()
            db.refresh(run_rec)

            try:
                # 1. COLLECT
                raw_posts = collector.collect(
                    brand_name=brand_name,
                    keywords=keywords,
                    competitors=competitors,
                    limit=limit_per_source
                )
                raw_posts = enrich_raw_posts(raw_posts)
                run_rec.records_found = len(raw_posts)

                posts_to_insert = []
                posts_by_id = {}
                analyses_to_insert = []
                posts_for_ai = []
                skipped_count = 0

                for raw in raw_posts:
                    # 2. NORMALIZE & DEDUPLICATE
                    content_hash = compute_content_hash(raw.content)
                    canonical_url = canonicalize_url(raw.url)

                    if is_duplicate_post(db, raw.source, raw.external_id, content_hash, canonical_url):
                        skipped_count += 1
                        continue

                    # 3. RELEVANCE FILTER
                    combined_text = f"{raw.title or ''} {raw.content}"
                    is_rel, rel_score, matched_entity = evaluate_relevance(
                        combined_text, keywords, product_names, competitors
                    )
                    if not is_rel:
                        skipped_count += 1
                        continue

                    # 4. LOCAL SENTIMENT (Free VADER)
                    sentiment_label, sentiment_score, needs_deeper_ai = analyze_local_sentiment(combined_text)

                    # 5. ENGAGEMENT & VIRALITY CALCULATION
                    pub_date = raw.published_at or utc_now()
                    eng_count, velocity, virality_score, virality_level, is_viral = calculate_engagement_and_virality(
                        likes=raw.likes,
                        comments=raw.comments,
                        shares=raw.shares,
                        published_at=pub_date,
                        source=raw.source
                    )

                    post = Post(
                        brand_id=brand.id,
                        source=raw.source,
                        external_id=raw.external_id,
                        url=canonical_url,
                        author=raw.author,
                        title=raw.title,
                        content=raw.content,
                        published_at=pub_date,
                        likes=raw.likes,
                        comments=raw.comments,
                        shares=raw.shares,
                        engagement_count=eng_count,
                        engagement_velocity=velocity,
                        raw_metadata=raw.raw_metadata,
                        content_hash=content_hash
                    )
                    db.add(post)
                    db.flush()  # assign post.id
                    persist_document_snapshot(db, post)

                    posts_to_insert.append(post)
                    posts_by_id[post.id] = post

                    # Prepare for batch AI processing
                    # Pass every new public record to the configured Gemini model.
                    posts_for_ai.append({
                        "id": post.id,
                        "title": post.title,
                        "content": post.content,
                        "source_url": post.url,
                        "local_sentiment": sentiment_label,
                        "sentiment_score": sentiment_score,
                        "virality_score": virality_score,
                        "virality_level": virality_level,
                        "is_viral": is_viral,
                        "needs_deeper_ai": needs_deeper_ai or is_viral,
                    })

                # 6. BATCH AI ANALYSIS (batches of settings.AI_BATCH_SIZE)
                ai_results_by_id = {}
                batch_size = settings.AI_BATCH_SIZE or 20

                gemini_error = None
                try:
                    for i in range(0, len(posts_for_ai), batch_size):
                        batch = posts_for_ai[i:i + batch_size]
                        ai_batch_output = ai_service.analyze_batch(batch)
                        for item in ai_batch_output:
                            ai_results_by_id[item.post_id] = item
                except GeminiError as exc:
                    # Collection must preserve verified source material and deterministic
                    # local signals when the optional provider is temporarily unavailable.
                    # A configured Gemini key continues to drive the normal path below.
                    gemini_error = str(exc)
                    logger.warning(
                        "Gemini analysis unavailable for collector %s; storing local analysis fallback: %s",
                        collector.source_name,
                        gemini_error,
                    )

                # 7. STORE ANALYSIS IN DATABASE
                for item_dict in posts_for_ai:
                    p_id = item_dict["id"]
                    ai_item = ai_results_by_id.get(p_id)

                    if ai_item is None and gemini_error is None:
                        raise RuntimeError(f"Gemini did not return analysis for post {p_id}.")

                    analysis = PostAnalysis(
                        post_id=p_id,
                        # Sentiment is derived locally so KPI, filters, and longitudinal
                        # reporting remain stable even when model phrasing changes.
                        sentiment=item_dict["local_sentiment"],
                        sentiment_score=item_dict["sentiment_score"],
                        topic=ai_item.topic if ai_item else None,
                        product=ai_item.product if ai_item else None,
                        competitor=ai_item.competitor if ai_item else None,
                        key_positive=ai_item.key_positive if ai_item else None,
                        key_negative=ai_item.key_negative if ai_item else None,
                        summary=ai_item.summary if ai_item else None,
                        recommendation=ai_item.recommendation if ai_item else None,
                        virality_score=item_dict["virality_score"],
                        virality_level=item_dict["virality_level"],
                        is_viral=item_dict["is_viral"],
                        analysis_version="1.0",
                        model_used=settings.GEMINI_MODEL if ai_item else "vader_heuristic",
                        analysis_provider="gemini" if ai_item else "local_heuristic",
                        analysis_status="completed" if ai_item else "fallback",
                    )
                    db.add(analysis)
                    db.flush()
                    persist_post_intelligence(db, posts_by_id[p_id], analysis, product_names)

                rebuild_issue_clusters(db, brand_id=brand.id)
                alerts = sync_reputation_alerts(db, brand_id=brand.id)
                dispatch_email_alerts(db, alerts)
                db.commit()

                if query_specs:
                    record_discovery_audit(
                        db=db,
                        brand_id=brand.id,
                        provider=collector.source_name,
                        specs=query_specs,
                        raw_posts=raw_posts,
                        started_at=run_rec.started_at,
                    )

                run_rec.records_added = len(posts_to_insert)
                run_rec.records_skipped = skipped_count
                run_rec.completed_at = utc_now()
                run_rec.status = "completed"
                db.commit()

                logger.info(
                    f"Collector {collector.source_name} finished. "
                    f"Found: {run_rec.records_found}, Added: {run_rec.records_added}, Skipped: {run_rec.records_skipped}"
                )

            except Exception as e:
                run_id = run_rec.id
                run_source = run_rec.source
                run_started_at = run_rec.started_at
                db.rollback()
                logger.error(f"Collector {collector.source_name} failed: {e}")
                if query_specs:
                    record_discovery_audit(
                        db=db,
                        brand_id=brand.id,
                        provider=collector.source_name,
                        specs=query_specs,
                        raw_posts=[],
                        started_at=run_started_at,
                        status="failed",
                        error_message=str(e),
                    )
                run_rec = db.get(CollectionRun, run_id)
                if run_rec is None:
                    run_rec = CollectionRun(
                        source=run_source,
                        started_at=run_started_at,
                    )
                    db.add(run_rec)
                run_rec.status = "failed"
                run_rec.error_message = str(e)
                run_rec.completed_at = utc_now()
                db.commit()

            run_records.append(run_rec)

        return run_records


collection_service = CollectionService()
