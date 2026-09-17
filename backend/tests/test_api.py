from datetime import datetime
from app.models.post import Post
from app.models.post_analysis import PostAnalysis
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
    assert data["gemini_model"] == "gemini-3.8-flash"


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


def test_invalid_pagination_parameters(client):
    # page=0 should return 422 Unprocessable Entity
    res_zero = client.get("/api/posts?page=0")
    assert res_zero.status_code == 422

    # page_size > 100 should return 422
    res_large = client.get("/api/posts?page_size=10000")
    assert res_large.status_code == 422


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
