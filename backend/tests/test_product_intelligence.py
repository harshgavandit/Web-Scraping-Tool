from datetime import timedelta

from app.intelligence.product_intelligence import (
    calculate_attention_score,
    calculate_reputation_risk,
    extract_aspect_evidence,
    resolve_product,
)
from app.utils.datetime_utils import utc_now
from app.models.post import Post
from app.models.post_analysis import PostAnalysis
from app.models.product_intelligence import Product, MentionEvidence, IssueCluster
from app.services.product_intelligence_service import persist_post_intelligence, rebuild_issue_clusters


def test_product_resolution_uses_configured_aliases_without_partial_false_matches():
    products = [
        {"name": "Pegasus 41", "aliases": ["Peg 41", "Air Zoom Pegasus 41"]},
        {"name": "Air Max", "aliases": ["Nike Air Max"]},
    ]

    assert resolve_product("My Peg 41 long-term review", products) == "Pegasus 41"
    assert resolve_product("The Jordan river is high", products) is None


def test_aspect_evidence_separates_praise_and_complaints_with_quotes():
    evidence = extract_aspect_evidence(
        "The Pegasus feels extremely comfortable and stable. "
        "However, the outsole wore out quickly and the price is too expensive."
    )

    by_aspect = {item.aspect: item for item in evidence}
    assert by_aspect["Comfort"].sentiment == "Positive"
    assert "comfortable" in by_aspect["Comfort"].quote
    assert by_aspect["Durability"].sentiment == "Negative"
    assert "wore out" in by_aspect["Durability"].quote
    assert by_aspect["Price & Value"].sentiment == "Negative"


def test_attention_score_uses_observable_google_signals_not_invented_engagement():
    score, level, reasons = calculate_attention_score(
        published_at=utc_now() - timedelta(hours=8),
        search_position=2,
        review_count=99,
        now=utc_now(),
    )

    assert score == 90.0
    assert level == "Surging"
    assert reasons == ["published in the last 24 hours", "top 3 Google result", "99 published reviews"]


def test_reputation_risk_requires_negative_evidence_and_source_diversity():
    score, level = calculate_reputation_risk(
        negative_mentions=12,
        unique_sources=5,
        growth_pct=80,
        average_confidence=0.9,
    )
    empty_score, empty_level = calculate_reputation_risk(0, 10, 300, 1.0)

    assert score == 83.0
    assert level == "Critical"
    assert (empty_score, empty_level) == (0.0, "Monitor")


def test_product_intelligence_persists_aspect_evidence_attention_and_risk_clusters(db_session):
    post = Post(
        brand_id=1,
        source="google_search",
        external_id="product-intelligence-1",
        url="https://reviews.example.org/pegasus",
        author="Runner Reviews",
        title="Nike Pegasus review",
        content="The Pegasus is comfortable. The outsole wore out quickly and the price is expensive.",
        content_hash="product-intelligence-hash-1",
        published_at=utc_now() - timedelta(hours=8),
        raw_metadata={
            "search_position": 2,
            "display_domain": "reviews.example.org",
            "page_fetch": {"product_data": {"review_count": 99}},
        },
    )
    db_session.add(post)
    db_session.flush()
    analysis = PostAnalysis(
        post_id=post.id,
        sentiment="Mixed",
        sentiment_score=-0.1,
        topic="Product Review",
        product="Pegasus",
    )
    db_session.add(analysis)
    db_session.flush()

    persist_post_intelligence(db_session, post, analysis, ["Pegasus"])
    rebuild_issue_clusters(db_session, brand_id=1, days=30)
    db_session.commit()

    product = db_session.query(Product).one()
    evidence = db_session.query(MentionEvidence).order_by(MentionEvidence.aspect).all()
    clusters = db_session.query(IssueCluster).all()
    assert product.name == "Pegasus"
    assert {item.aspect for item in evidence} >= {"Comfort", "Durability", "Price & Value"}
    assert analysis.attention_score == 90.0 # type: ignore
    assert analysis.attention_level == "Surging"
    assert analysis.is_viral is False
    assert any(str(cluster.aspect) == "Durability" and cluster.mention_count == 1 for cluster in clusters)


def test_intelligence_overview_returns_product_praise_complaints_and_risks(client, db_session):
    post = Post(
        brand_id=1,
        source="google_search",
        external_id="product-intelligence-api-1",
        url="https://reviews.example.org/pegasus-api",
        title="Nike Pegasus review",
        content="The Pegasus is comfortable, but the outsole wore out quickly.",
        content_hash="product-intelligence-api-hash-1",
        published_at=utc_now(),
        raw_metadata={"search_position": 1, "display_domain": "reviews.example.org"},
    )
    db_session.add(post)
    db_session.flush()
    analysis = PostAnalysis(post_id=post.id, sentiment="Mixed", sentiment_score=-0.1, topic="Review", product="Pegasus", competitor="Adidas")
    db_session.add(analysis)
    db_session.flush()
    persist_post_intelligence(db_session, post, analysis, ["Pegasus"])
    rebuild_issue_clusters(db_session, brand_id=1, days=30)
    db_session.commit()

    response = client.get("/api/intelligence/overview?brand_id=1&days=30")

    assert response.status_code == 200
    payload = response.json()
    assert payload["products"][0]["product"] == "Pegasus"
    assert payload["products"][0]["top_praise"] == "Comfort"
    assert payload["products"][0]["top_complaint"] == "Durability"
    assert any(str(item["aspect"]) == "Durability" for item in payload["risks"])
    assert any(str(item["aspect"]) == "Comfort" for item in payload["praises"])
    assert any(item["competitor"] == "Adidas" for item in payload["competitors"])


def test_rebuild_endpoint_backfills_existing_real_posts(client, db_session):
    post = Post(
        brand_id=1,
        source="news_rss",
        external_id="existing-real-review",
        url="https://reviews.example.org/existing-pegasus",
        title="Nike Pegasus long-term review",
        content="The Pegasus is comfortable, but the outsole wore out quickly and the price is expensive.",
        content_hash="existing-real-review-hash",
        published_at=utc_now(),
        raw_metadata={"feed": "Google News RSS", "engagement_available": False},
    )
    db_session.add(post)
    db_session.flush()
    db_session.add(PostAnalysis(
        post_id=post.id,
        sentiment="Mixed",
        sentiment_score=-0.2,
        product="Pegasus",
        topic="Product Review",
    ))
    db_session.commit()

    response = client.post("/api/intelligence/rebuild?brand_id=1")

    assert response.status_code == 200
    assert response.json()["posts_processed"] == 1
    overview = client.get("/api/intelligence/overview?brand_id=1&days=30").json()
    assert overview["products"][0]["product"] == "Pegasus"
    assert overview["products"][0]["top_praise"] == "Comfort"
    assert any(item["aspect"] == "Durability" for item in overview["risks"])


def test_multilingual_aspect_extraction_french_and_spanish():
    french = extract_aspect_evidence("Cette chaussure est très confortable mais le prix est trop cher.")
    spanish = extract_aspect_evidence("La amortiguacion es excelente. El precio es caro.")

    fr_aspects = {item.aspect: item for item in french}
    es_aspects = {item.aspect: item for item in spanish}

    assert "Price & Value" in fr_aspects or "Comfort" in fr_aspects
    assert es_aspects["Price & Value"].sentiment == "Negative"
