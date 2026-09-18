import inspect
from datetime import datetime, timedelta
from app.api.collection import trigger_collection
from app.models.post import Post
from app.models.post_analysis import PostAnalysis
from app.models.competitor import Competitor
from app.models.tracked_keyword import TrackedKeyword
from app.models.search_discovery import SearchQuery, SearchRun, SearchResult
from app.schemas.post_analysis import AIAnalysisItem
from app.core.config import settings
from app.utils.datetime_utils import utc_now


def test_api_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("ok", "degraded")
    assert "version" in data
    assert data["ai_provider"] == "gemini"
    assert data["gemini_model"] == "gemini-3.5-flash"


def test_collection_trigger_declares_background_tasks_as_a_fastapi_dependency():
    parameter = inspect.signature(trigger_collection).parameters["background_tasks"]

    assert parameter.default is inspect.Signature.empty


def test_collection_health_reports_google_discovery_coverage(client, db_session):
    query = SearchQuery(
        brand_id=1,
        provider="google_search",
        query='"Nike" review',
        category="customer_feedback",
        country="US",
        language="en",
    )
    db_session.add(query)
    db_session.flush()
    run = SearchRun(
        query_id=query.id,
        provider="google_search",
        status="completed",
        results_found=1,
        results_new=1,
        completed_at=utc_now(),
    )
    db_session.add(run)
    db_session.flush()
    db_session.add(SearchResult(
        query_id=query.id,
        search_run_id=run.id,
        provider="google_search",
        title="Nike customer review",
        snippet="A public review",
        url="https://reviews.example.org/nike",
        display_domain="reviews.example.org",
        position=1,
        country="US",
        language="en",
    ))
    db_session.commit()

    response = client.get("/api/collection/health?brand_id=1")

    assert response.status_code == 200
    assert response.json() == {
        "brand_id": 1,
        "configured_queries": 1,
        "successful_query_runs": 1,
        "failed_query_runs": 0,
        "discovered_results": 1,
        "unique_domains": 1,
        "last_successful_discovery": response.json()["last_successful_discovery"],
    }
    assert response.json()["last_successful_discovery"] is not None


def test_api_brands(client):
    res = client.get("/api/brands")
    assert res.status_code == 200
    brands = res.json()
    assert len(brands) >= 1
    assert brands[0]["name"] == "Nike"


def test_posts_pagination_and_filters(client, db_session):
    # Insert 3 test posts
    for i in range(1, 4):
        p = Post(
            brand_id=1,
            source="reddit" if i % 2 == 0 else "twitter",
            external_id=f"test_post_{i}",
            content=f"Post content {i} discussing Nike Pegasus and comfort",
            title=f"Test Post {i}",
            content_hash=f"hash_{i}",
            published_at=utc_now(),
            likes=100 * i
        )
        db_session.add(p)
        db_session.flush()

        a = PostAnalysis(
            post_id=p.id,
            sentiment="Positive" if i == 1 else "Negative",
            topic="Comfort",
            product="Pegasus",
            competitor="Adidas" if i == 1 else "Puma",
            virality_score=88.0 if i == 1 else 30.0,
            virality_level="Viral" if i == 1 else "Low",
            is_viral=(i == 1)
        )
        db_session.add(a)
    db_session.commit()

    # 1. Test pagination
    res = client.get("/api/posts?page=1&page_size=2")
    assert res.status_code == 200
    data = res.json()
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert len(data["items"]) == 2
    assert data["total"] >= 3

    # 2. Test sentiment filter
    res_pos = client.get("/api/posts?sentiment=Positive")
    assert res_pos.status_code == 200
    pos_items = res_pos.json()["items"]
    assert all(item["analysis"]["sentiment"] == "Positive" for item in pos_items)

    # 3. Test viral filter
    res_viral = client.get("/api/posts?viral=true")
    assert res_viral.status_code == 200
    viral_items = res_viral.json()["items"]
    assert all(item["analysis"]["is_viral"] is True for item in viral_items)

    # 4. Test search
    res_search = client.get("/api/posts?search=Pegasus")
    assert res_search.status_code == 200
    assert len(res_search.json()["items"]) >= 1

    # 5. Test competitor filter
    res_comp = client.get("/api/posts?competitor=Adidas")
    assert res_comp.status_code == 200
    comp_items = res_comp.json()["items"]
    assert len(comp_items) >= 1
    assert all("Adidas" in (item["analysis"]["competitor"] or "") for item in comp_items)


def test_competitor_filter_matches_original_conversation_text(client, db_session):
    post = Post(
        brand_id=1,
        source="news_rss",
        external_id="content_competitor_match",
        content="Runners compare Nike cushioning with New Balance pricing.",
        title="Nike versus New Balance",
        content_hash="content_competitor_match_hash",
        published_at=utc_now(),
    )
    db_session.add(post)
    db_session.flush()
    db_session.add(PostAnalysis(
        post_id=post.id,
        sentiment="Mixed",
        topic="Pricing & Value",
        competitor=None,
        virality_score=0,
        virality_level="Low",
        is_viral=False,
    ))
    db_session.commit()

    response = client.get("/api/posts?competitor=New%20Balance")

    assert response.status_code == 200
    assert [item["external_id"] for item in response.json()["items"]] == ["content_competitor_match"]


def test_any_competitor_filter_returns_all_competitor_conversations(client, db_session):
    for index, competitor in enumerate(("Puma", "Under Armour"), start=1):
        post = Post(
            brand_id=1,
            source="news_rss",
            external_id=f"any_competitor_{index}",
            content=f"Nike compared with {competitor} for runners.",
            title=f"Nike versus {competitor}",
            content_hash=f"any_competitor_hash_{index}",
            published_at=utc_now(),
        )
        db_session.add(post)
        db_session.flush()
        db_session.add(PostAnalysis(post_id=post.id, sentiment="Mixed", competitor=competitor))
    db_session.commit()

    response = client.get("/api/posts?competitor=any")

    assert response.status_code == 200
    assert {item["external_id"] for item in response.json()["items"]} == {
        "any_competitor_1", "any_competitor_2",
    }


def test_viral_filter_uses_observable_attention_for_google_content(client, db_session):
    post = Post(
        brand_id=1,
        source="google_search",
        external_id="high_attention_google",
        content="A highly visible Nike Pegasus review.",
        title="Nike Pegasus review",
        content_hash="high_attention_google_hash",
        published_at=utc_now(),
        raw_metadata={"engagement_available": False},
    )
    db_session.add(post)
    db_session.flush()
    db_session.add(PostAnalysis(
        post_id=post.id,
        sentiment="Positive",
        is_viral=False,
        virality_score=0,
        attention_score=72,
        attention_level="High attention",
    ))
    db_session.commit()

    response = client.get("/api/posts?viral=true&sort_by=highest_virality")

    assert response.status_code == 200
    assert [item["external_id"] for item in response.json()["items"]] == ["high_attention_google"]


def test_invalid_pagination_parameters(client):
    # page=0 should return 422 Unprocessable Entity
    res_zero = client.get("/api/posts?page=0")
    assert res_zero.status_code == 422

    # page_size > 100 should return 422
    res_large = client.get("/api/posts?page_size=10000")
    assert res_large.status_code == 422


def test_posts_date_range_filter_excludes_older_conversations(client, db_session):
    now = utc_now()
    recent = Post(
        brand_id=1,
        source="reddit",
        external_id="date_filter_recent",
        content="Recent Nike conversation",
        title="Recent conversation",
        content_hash="date_filter_recent_hash",
        published_at=now - timedelta(days=2),
    )
    older = Post(
        brand_id=1,
        source="reddit",
        external_id="date_filter_older",
        content="Older Nike conversation",
        title="Older conversation",
        content_hash="date_filter_older_hash",
        published_at=now - timedelta(days=10),
    )
    db_session.add_all([recent, older])
    db_session.commit()

    response = client.get(
        "/api/posts",
        params={"brand_id": 1, "date_from": (now - timedelta(days=7)).isoformat()},
    )

    assert response.status_code == 200
    external_ids = {item["external_id"] for item in response.json()["items"]}
    assert "date_filter_recent" in external_ids
    assert "date_filter_older" not in external_ids


def test_invalid_filter_and_sort_values_are_rejected(client):
    assert client.get("/api/posts?source=unknown-network").status_code == 422
    assert client.get("/api/posts?sentiment=Excellent").status_code == 422
    assert client.get("/api/posts?virality_level=Extreme").status_code == 422
    assert client.get("/api/posts?sort_by=random").status_code == 422


def test_mutating_api_payloads_validate_names_categories_and_sources(client):
    assert client.post("/api/brands", json={"name": "   "}).status_code == 422
    assert client.post(
        "/api/brands/1/keywords",
        json={"keyword": "Nike", "category": "unsupported", "active": True},
    ).status_code == 422
    assert client.post(
        "/api/brands/1/competitors",
        json={"name": ""},
    ).status_code == 422
    assert client.post(
        "/api/collection/run",
        json={"source": "untrusted", "brand_id": 1},
    ).status_code == 422
    assert client.post(
        "/api/collection/run",
        json={"source": "mock", "brand_id": 1},
    ).status_code == 422
    assert client.get("/api/posts?source=mock").status_code == 422


def test_brand_configuration_rejects_duplicates_and_deletes_owned_items(client, db_session):
    competitor = db_session.query(Competitor).filter_by(brand_id=1, name="Adidas").one()
    keyword = db_session.query(TrackedKeyword).filter_by(brand_id=1, keyword="Pegasus").one()

    duplicate_competitor = client.post("/api/brands/1/competitors", json={"name": " adidas "})
    duplicate_keyword = client.post(
        "/api/brands/1/keywords",
        json={"keyword": " pegasus ", "category": "product", "active": True},
    )
    deleted_competitor = client.delete(f"/api/brands/1/competitors/{competitor.id}")
    deleted_keyword = client.delete(f"/api/brands/1/keywords/{keyword.id}")

    assert duplicate_competitor.status_code == 409
    assert duplicate_keyword.status_code == 409
    assert deleted_competitor.status_code == 204
    assert deleted_keyword.status_code == 204
    assert db_session.get(Competitor, competitor.id) is None
    assert db_session.get(TrackedKeyword, keyword.id) is None


def test_brand_configuration_cannot_delete_an_item_owned_by_another_brand(client, db_session):
    assert client.delete("/api/brands/999/competitors/1").status_code == 404
    assert client.delete("/api/brands/999/keywords/1").status_code == 404


def test_manual_analysis_batches_posts_and_preserves_local_sentiment(client, db_session, monkeypatch):
    for i in range(25):
        db_session.add(Post(
            brand_id=1,
            source="reddit",
            external_id=f"analysis_batch_{i}",
            content=f"Nike shoes are terrible and disappointing number {i}",
            title=f"Bad Nike review {i}",
            content_hash=f"analysis_batch_hash_{i}",
            published_at=utc_now(),
        ))
    db_session.commit()

    batch_sizes = []

    def fake_analyze(posts):
        batch_sizes.append(len(posts))
        return [
            AIAnalysisItem(
                post_id=post["id"],
                sentiment="Positive",
                topic="Build Quality & Durability",
                summary="AI supplied contextual summary.",
                recommendation="Investigate the recurring complaint.",
            )
            for post in posts
        ]

    monkeypatch.setattr("app.api.analysis.ai_service.analyze_batch", fake_analyze)
    previous_batch_size = settings.AI_BATCH_SIZE
    settings.AI_BATCH_SIZE = 20
    try:
        response = client.post("/api/analysis/run?brand_id=1&limit=25")
    finally:
        settings.AI_BATCH_SIZE = previous_batch_size

    assert response.status_code == 200
    assert response.json()["analyzed"] == 25
    assert batch_sizes == [20, 5]
    analyses = db_session.query(PostAnalysis).join(Post).filter(
        Post.external_id.like("analysis_batch_%")
    ).all()
    assert len(analyses) == 25
    assert all(item.sentiment == "Negative" for item in analyses)
    assert all(item.sentiment_score < 0 for item in analyses)


def test_single_post_live_analysis_persists_unique_gemini_result(client, db_session, monkeypatch):
    post = Post(
        brand_id=1,
        source="news_rss",
        external_id="live-gemini-story",
        content="Nike unveiled a Pegasus trail edition with a waterproof upper for winter runners.",
        title="Nike adds a waterproof Pegasus trail edition",
        content_hash="live-gemini-story-hash",
        published_at=utc_now(),
    )
    db_session.add(post)
    db_session.flush()
    db_session.add(PostAnalysis(
        post_id=post.id,
        sentiment="Neutral",
        summary="General brand chatter discussing brand discussion with neutral reception.",
        model_used="vader_heuristic",
        analysis_provider="local_heuristic",
        analysis_status="fallback",
    ))
    db_session.commit()

    def analyze(posts):
        return [AIAnalysisItem(
            post_id=post.id,
            sentiment="Positive",
            topic="Running & Performance",
            product="Pegasus",
            summary="Nike introduced a waterproof Pegasus trail edition aimed at winter runners.",
            key_positive="Waterproof upper",
            recommendation="Explain the winter-weather benefits in trail-running campaigns.",
            analysis_provider="gemini",
            analysis_status="completed",
        )]

    monkeypatch.setattr("app.api.analysis.ai_service.analyze_batch", analyze)
    response = client.post(f"/api/analysis/posts/{post.id}/refresh")

    assert response.status_code == 200
    payload = response.json()
    assert payload["analysis"]["summary"] == "Nike introduced a waterproof Pegasus trail edition aimed at winter runners."
    assert payload["analysis"]["analysis_provider"] == "gemini"
    assert payload["analysis"]["analysis_status"] == "completed"
    assert payload["analysis"]["model_used"] == settings.GEMINI_MODEL


def test_dashboard_summary_api(client, db_session):
    res = client.get("/api/dashboard/summary?brand_id=1")
    assert res.status_code == 200
    data = res.json()
    assert "kpis" in data
    assert "executive_summary" in data
    assert "total_mentions" in data["kpis"]


def test_empty_dataset_dashboard_summary(client):
    # Brand 9999 has no posts
    res = client.get("/api/dashboard/summary?brand_id=9999")
    assert res.status_code == 200
    data = res.json()
    assert data["kpis"]["total_mentions"] == 0
    assert data["executive_summary"]["positive_pct"] == 0.0


def test_topics_api(client, db_session):
    res = client.get("/api/topics?brand_id=1")
    assert res.status_code == 200
    topics = res.json()
    assert isinstance(topics, list)
