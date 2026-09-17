from sqlalchemy import event

from app.analytics.summary_generator import generate_dashboard_summary
from app.models.post import Post
from app.models.post_analysis import PostAnalysis
from datetime import timedelta

from app.utils.datetime_utils import utc_now


def test_dashboard_summary_uses_correct_kpis_without_loading_all_post_bodies(db_session):
    fixtures = [
        ("Positive", 0.8, "Comfort", False, 35.0),
        ("Positive", 0.7, "Comfort", True, 90.0),
        ("Negative", -0.8, "Pricing", False, 55.0),
        ("Mixed", 0.0, "Pricing", False, 45.0),
    ]
    for index, (sentiment, score, topic, is_viral, virality) in enumerate(fixtures):
        post = Post(
            brand_id=1,
            source="reddit",
            external_id=f"dashboard_fixture_{index}",
            title=f"Dashboard fixture {index}",
            content=f"Large external post body {index}",
            content_hash=f"dashboard_fixture_hash_{index}",
            published_at=utc_now(),
        )
        db_session.add(post)
        db_session.flush()
        db_session.add(PostAnalysis(
            post_id=post.id,
            sentiment=sentiment,
            sentiment_score=score,
            topic=topic,
            virality_score=virality,
            virality_level="Viral" if is_viral else "Medium",
            is_viral=is_viral,
        ))
    db_session.commit()

    statements = []

    def capture_sql(_conn, _cursor, statement, _params, _context, _executemany):
        statements.append(statement.lower())

    event.listen(db_session.bind, "before_cursor_execute", capture_sql)
    try:
        result = generate_dashboard_summary(db_session, brand_id=1, days=30, force_refresh=True)
    finally:
        event.remove(db_session.bind, "before_cursor_execute", capture_sql)

    assert result.kpis.total_mentions == 4
    assert result.kpis.positive_pct == 50.0
    assert result.kpis.negative_pct == 25.0
    assert result.kpis.mixed_pct == 25.0
    assert result.kpis.neutral_pct == 0.0
    assert result.kpis.viral_posts_count == 1
    assert result.kpis.top_positive_topic == "Comfort"
    assert result.kpis.top_complaint == "Pricing"
    dashboard_sql = "\n".join(statements)
    assert ".content as " not in dashboard_sql
    assert ".raw_metadata as " not in dashboard_sql


def test_dashboard_cache_invalidates_when_stored_analysis_changes(db_session):
    post = Post(
        brand_id=1,
        source="reddit",
        external_id="dashboard_cache_fixture",
        title="Cache fixture",
        content="Nike cache fixture",
        content_hash="dashboard_cache_fixture_hash",
        published_at=utc_now(),
    )
    db_session.add(post)
    db_session.flush()
    analysis = PostAnalysis(
        post_id=post.id,
        sentiment="Positive",
        sentiment_score=0.8,
        topic="Comfort",
        virality_score=10,
        virality_level="Low",
        is_viral=False,
    )
    db_session.add(analysis)
    db_session.commit()

    initial = generate_dashboard_summary(db_session, brand_id=1, days=30, force_refresh=True)
    assert initial.kpis.positive_pct == 100.0

    analysis.sentiment = "Negative"
    analysis.sentiment_score = -0.8
    analysis.topic = "Pricing"
    analysis.analyzed_at = utc_now() + timedelta(seconds=1)
    db_session.commit()

    refreshed = generate_dashboard_summary(db_session, brand_id=1, days=30)
    assert refreshed.kpis.negative_pct == 100.0
    assert refreshed.kpis.top_complaint == "Pricing"
