from app.collectors import get_collectors
from app.collectors.reddit import RedditCollector
from app.collectors.facebook import FacebookCollector
from app.collectors.rss import (
    RSSCollector,
    PublisherRSSCollector,
    build_google_news_queries,
)
from app.collectors.google_search import GoogleSearchCollector
from app.discovery.query_planner import build_google_query_specs
from app.discovery.query_planner import GoogleQuerySpec
from app.models.search_discovery import SearchQuery, SearchRun, SearchResult
from app.models.document import Document, DocumentSnapshot
from app.extraction.page_extractor import ExtractedDocument
from app.services.page_fetch_service import PageFetchResult
from app.services.collection_service import collection_service
from app.collectors.base import BaseCollector, RawPost
from app.models.post import Post
from app.models.post_analysis import PostAnalysis
from app.schemas.post_analysis import AIAnalysisItem
from app.utils.datetime_utils import utc_now
from unittest.mock import MagicMock, patch


def test_reddit_collector_returns_no_data_when_not_configured(monkeypatch):
    monkeypatch.setattr("app.collectors.reddit.settings.REDDIT_ENABLED", False)
    collector = RedditCollector()
    posts = collector.collect("Nike", ["Nike"], ["Adidas"], limit=5)
    assert posts == []


def test_facebook_collector_returns_no_data_when_not_configured(monkeypatch):
    monkeypatch.setattr("app.collectors.facebook.settings.FACEBOOK_ENABLED", False)
    collector = FacebookCollector()
    posts = collector.collect("Nike", ["Nike"], ["Adidas"], limit=5)
    assert posts == []


def test_facebook_collector_uses_graph_api_permalink(monkeypatch):
    monkeypatch.setattr("app.collectors.facebook.settings.FACEBOOK_ENABLED", True)
    monkeypatch.setattr("app.collectors.facebook.settings.FACEBOOK_ACCESS_TOKEN", "test-token")
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "data": [{
            "id": "123_456",
            "message": "Nike Pegasus customer feedback",
            "permalink_url": "https://www.facebook.com/nike/posts/456",
            "created_time": "2026-09-16T10:00:00+0000",
            "likes": {"summary": {"total_count": 12}},
            "comments": {"summary": {"total_count": 3}},
            "shares": {"count": 1},
        }]
    }

    with patch("httpx.Client.get", return_value=response):
        posts = FacebookCollector().collect("Nike", ["Nike"], ["Adidas"], limit=5)

    assert len(posts) == 1
    assert posts[0].url == "https://www.facebook.com/nike/posts/456"


def test_all_collectors_excludes_disabled_sources(monkeypatch):
    monkeypatch.setattr("app.collectors.google_search.settings.GOOGLE_SEARCH_ENABLED", True)
    monkeypatch.setattr("app.collectors.google_search.settings.GOOGLE_SEARCH_API_KEY", "search-key")
    monkeypatch.setattr("app.collectors.google_search.settings.GOOGLE_SEARCH_ENGINE_ID", "engine-id")

    sources = {collector.source_name for collector in get_collectors("all")}

    assert sources == {"rss", "publisher_rss", "google_search"}


def test_unknown_collector_source_does_not_fall_back_to_generated_data():
    assert get_collectors("mock") == []
    assert get_collectors("unknown") == []


def test_rss_collector_parses_public_feed_without_ai_or_credentials():
    response = MagicMock()
    response.status_code = 200
    response.content = b"""<?xml version='1.0' encoding='UTF-8'?>
    <rss><channel><item>
      <title>Nike Pegasus launch review</title>
      <link>https://example.com/nike-pegasus</link>
      <guid>nike-pegasus-guid</guid>
      <pubDate>Tue, 16 Sep 2026 10:00:00 GMT</pubDate>
      <description><![CDATA[<p>Runners praise the new Nike shoe.</p>]]></description>
    </item></channel></rss>"""

    with patch("httpx.Client.get", return_value=response):
        posts = RSSCollector().collect("Nike", ["Nike"], ["Adidas"], limit=5)

    assert len(posts) == 1
    assert posts[0].source == "news_rss"
    assert posts[0].external_id == "nike-pegasus-guid"
    assert "Runners praise" in posts[0].content
    assert posts[0].url == "https://example.com/nike-pegasus"
    assert (posts[0].likes, posts[0].comments, posts[0].shares) == (0, 0, 0)


def test_publisher_rss_collector_keeps_nike_articles_and_uses_the_original_article_url(monkeypatch):
    """A publisher feed must not send a feed or tracking URL to the dashboard."""
    monkeypatch.setattr("app.collectors.rss.settings.PUBLISHER_RSS_ENABLED", True, raising=False)
    monkeypatch.setattr(
        "app.collectors.rss.settings.PUBLISHER_RSS_FEEDS",
        "Runner Journal|https://feeds.example.test/nike.xml",
        raising=False,
    )
    response = MagicMock()
    response.status_code = 200
    response.content = b"""<?xml version='1.0' encoding='UTF-8'?>
    <rss><channel>
      <item>
        <title>Nike Pegasus gets a runner review</title>
        <link>https://publisher.example.test/reviews/nike-pegasus?utm_source=rss</link>
        <guid>publisher-nike-1</guid>
        <pubDate>Tue, 16 Sep 2026 10:00:00 GMT</pubDate>
        <description><![CDATA[<p>Nike runners praise the new Pegasus.</p>]]></description>
      </item>
      <item>
        <title>Unrelated football transfer</title>
        <link>https://publisher.example.test/sport/transfer</link>
        <guid>publisher-other-1</guid>
        <description>Nothing about the tracked brand.</description>
      </item>
    </channel></rss>"""

    with patch("httpx.Client.get", return_value=response):
        posts = PublisherRSSCollector().collect("Nike", ["Nike", "Pegasus"], ["Adidas"], limit=5)

    assert len(posts) == 1
    assert posts[0].source == "publisher_rss"
    assert posts[0].url == "https://publisher.example.test/reviews/nike-pegasus"
    assert posts[0].raw_metadata["feed_name"] == "Runner Journal"
    assert posts[0].raw_metadata["feed_url"] == "https://feeds.example.test/nike.xml"
    assert posts[0].raw_metadata["original_feed_url"].endswith("utm_source=rss")


def test_publisher_rss_collector_parses_atom_entries_with_alternate_article_links(monkeypatch):
    monkeypatch.setattr("app.collectors.rss.settings.PUBLISHER_RSS_ENABLED", True, raising=False)
    monkeypatch.setattr(
        "app.collectors.rss.settings.PUBLISHER_RSS_FEEDS",
        "Sneaker Desk|https://feeds.example.test/sneakers.atom",
        raising=False,
    )
    response = MagicMock()
    response.status_code = 200
    response.content = b"""<?xml version='1.0' encoding='UTF-8'?>
    <feed xmlns='http://www.w3.org/2005/Atom'>
      <entry>
        <id>urn:publisher:nike-atom-1</id>
        <title>Nike launches a new Air Max colorway</title>
        <link rel='self' href='https://feeds.example.test/entries/1'/>
        <link rel='alternate' href='https://publisher.example.test/news/air-max#details'/>
        <updated>2026-09-16T10:00:00Z</updated>
        <summary>Nike expands the Air Max line.</summary>
      </entry>
    </feed>"""

    with patch("httpx.Client.get", return_value=response):
        posts = PublisherRSSCollector().collect("Nike", ["Nike", "Air Max"], [], limit=5)

    assert len(posts) == 1
    assert posts[0].external_id == "urn:publisher:nike-atom-1"
    assert posts[0].url == "https://publisher.example.test/news/air-max"
    assert "Air Max" in posts[0].content


def test_google_news_queries_cover_feedback_products_trends_competitors_and_blogs():
    queries = build_google_news_queries(
        "Nike",
        ["Nike", "Pegasus", "Air Max"],
        ["Adidas", "Puma"],
    )

    categories = {category for category, _ in queries}
    query_text = " ".join(query for _, query in queries)
    assert {
        "overall_presence",
        "customer_feedback",
        "viral_trending",
        "competitor_comparison",
        "articles_blogs",
        "tracked_topic",
    }.issubset(categories)
    assert "Pegasus" in query_text
    assert "Air Max" in query_text
    assert "Adidas" in query_text
    competitor_queries = [
        query for category, query in queries if category == "competitor_comparison"
    ]
    assert len(competitor_queries) == 2
    assert any('"Adidas"' in query and '"Puma"' not in query for query in competitor_queries)
    assert any('"Puma"' in query and '"Adidas"' not in query for query in competitor_queries)


def test_rss_collector_deduplicates_results_across_google_queries_and_records_provenance():
    response = MagicMock()
    response.status_code = 200
    response.content = b"""<?xml version='1.0' encoding='UTF-8'?>
    <rss><channel><item>
      <title>Nike Pegasus customer review</title>
      <link>https://news.google.com/rss/articles/real-review</link>
      <guid>shared-google-guid</guid>
      <pubDate>Tue, 16 Sep 2026 10:00:00 GMT</pubDate>
      <source url="https://publisher.example">Runner Reviews</source>
      <description><![CDATA[Customers discuss Nike Pegasus comfort.]]></description>
    </item></channel></rss>"""

    with patch("httpx.Client.get", return_value=response) as get:
        posts = RSSCollector().collect(
            "Nike",
            ["Nike", "Pegasus"],
            ["Adidas"],
            limit=20,
        )

    assert get.call_count >= 6
    assert len(posts) == 1
    assert posts[0].author == "Runner Reviews"
    assert posts[0].raw_metadata["discovery_category"] == "overall_presence"
    assert posts[0].raw_metadata["google_query"]
    assert posts[0].raw_metadata["publisher_url"] == "https://publisher.example"


def test_query_planner_builds_product_feedback_risk_and_separate_competitor_queries():
    specs = build_google_query_specs(
        "Nike",
        ["Nike", "Pegasus", "Air Max"],
        ["Adidas", "Puma"],
    )

    categories = {spec.category for spec in specs}
    assert {"brand_presence", "customer_feedback", "reputation_risk", "product_review", "competitor_comparison"}.issubset(categories)
    assert any(spec.product == "Pegasus" and '"Pegasus"' in spec.query for spec in specs)
    assert any(spec.competitor == "Adidas" and '"Puma"' not in spec.query for spec in specs)
    assert any(spec.competitor == "Puma" and '"Adidas"' not in spec.query for spec in specs)


def test_google_search_collector_extracts_google_results_with_query_provenance(monkeypatch):
    monkeypatch.setattr("app.collectors.google_search.settings.GOOGLE_SEARCH_ENABLED", True)
    monkeypatch.setattr("app.collectors.google_search.settings.GOOGLE_SEARCH_API_KEY", "search-key")
    monkeypatch.setattr("app.collectors.google_search.settings.GOOGLE_SEARCH_ENGINE_ID", "engine-id")
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "items": [{
            "cacheId": "google-result-1",
            "title": "Nike Pegasus customer review",
            "link": "https://reviews.example.org/nike-pegasus",
            "displayLink": "reviews.example.org",
            "snippet": "Customers discuss comfort and pricing.",
            "pagemap": {"metatags": [{"article:published_time": "2026-09-16T10:00:00Z"}]},
        }]
    }

    with patch("httpx.Client.get", return_value=response):
        posts = GoogleSearchCollector().collect("Nike", ["Nike", "Pegasus"], ["Adidas"], limit=5)

    assert len(posts) == 1
    assert posts[0].source == "google_search"
    assert posts[0].url == "https://reviews.example.org/nike-pegasus"
    assert posts[0].raw_metadata["google_query"]
    assert posts[0].raw_metadata["display_domain"] == "reviews.example.org"
    assert posts[0].raw_metadata["search_position"] == 1
    assert (posts[0].likes, posts[0].comments, posts[0].shares) == (0, 0, 0)


class _FailingCollector(BaseCollector):
    @property
    def source_name(self):
        return "failing"

    def is_enabled(self):
        return True

    def collect(self, brand_name, keywords, competitors, limit=50):
        raise RuntimeError("collector unavailable")


class _SuccessfulCollector(BaseCollector):
    def __init__(self, external_id="collector_isolation_1"):
        self.external_id = external_id

    @property
    def source_name(self):
        return "successful"

    def is_enabled(self):
        return True

    def collect(self, brand_name, keywords, competitors, limit=50):
        return [RawPost(
            source="web",
            external_id=self.external_id,
            title="Nike running shoes",
            content="Nike running shoes are comfortable and excellent.",
            published_at=utc_now(),
            likes=10,
        )]


class _AuditedGoogleCollector(_SuccessfulCollector):
    @property
    def source_name(self):
        return "google_search"

    def build_queries(self, brand_name, keywords, competitors):
        return [GoogleQuerySpec(
            category="product_review",
            query='"Nike" "Pegasus" review',
            product="Pegasus",
        )]

    def collect(self, brand_name, keywords, competitors, limit=50):
        post = super().collect(brand_name, keywords, competitors, limit)[0]
        post.source = "google_search"
        post.url = "https://reviews.example.org/pegasus"
        post.raw_metadata = {
            "provider": "google",
            "google_query": '"Nike" "Pegasus" review',
            "discovery_category": "product_review",
            "search_position": 2,
            "display_domain": "reviews.example.org",
            "country": "US",
            "language": "en",
        }
        return [post]


def test_one_failed_collector_does_not_stop_following_collectors(db_session, monkeypatch):
    monkeypatch.setattr(
        "app.services.collection_service.get_collectors",
        lambda source: [_FailingCollector(), _SuccessfulCollector()],
    )
    runs = collection_service.run_pipeline(db_session, brand_id=1, source="all")

    assert [run.status for run in runs] == ["failed", "completed"]
    assert runs[1].records_added == 1


def test_collection_keeps_local_sentiment_and_does_not_reanalyze_duplicates(db_session, monkeypatch):
    external_id = "collector_local_sentiment_1"
    collector = _SuccessfulCollector(external_id)
    monkeypatch.setattr(
        "app.services.collection_service.get_collectors",
        lambda source: [collector],
    )
    call_count = 0

    def fake_analyze(posts):
        nonlocal call_count
        call_count += 1
        return [AIAnalysisItem(
            post_id=post["id"],
            sentiment="Negative",
            topic="Running & Performance",
            summary="AI supplied summary.",
            recommendation="Use comfort testimonials.",
        ) for post in posts]

    monkeypatch.setattr("app.services.collection_service.ai_service.analyze_batch", fake_analyze)

    first = collection_service.run_pipeline(db_session, brand_id=1, source="successful")
    second = collection_service.run_pipeline(db_session, brand_id=1, source="successful")

    assert first[0].records_added == 1
    assert second[0].records_added == 0
    assert call_count == 1
    post = db_session.query(Post).filter(Post.external_id == external_id).one()
    analysis = db_session.query(PostAnalysis).filter(PostAnalysis.post_id == post.id).one()
    assert analysis.sentiment == "Positive"


def test_google_collection_persists_query_run_and_result_audit(db_session, monkeypatch):
    monkeypatch.setattr(
        "app.services.collection_service.get_collectors",
        lambda source: [_AuditedGoogleCollector("google-audit-1")],
    )

    runs = collection_service.run_pipeline(db_session, brand_id=1, source="google_search")

    assert runs[0].status == "completed"
    query = db_session.query(SearchQuery).one()
    search_run = db_session.query(SearchRun).one()
    result = db_session.query(SearchResult).one()
    assert query.query == '"Nike" "Pegasus" review'
    assert query.category == "product_review"
    assert search_run.status == "completed"
    assert search_run.results_found == 1
    assert result.url == "https://reviews.example.org/pegasus"
    assert result.position == 2


def test_google_collection_fetches_original_page_and_persists_evidence_snapshot(db_session, monkeypatch):
    monkeypatch.setattr(
        "app.services.collection_service.get_collectors",
        lambda source: [_AuditedGoogleCollector("google-original-page-1")],
    )
    monkeypatch.setattr("app.services.collection_service.settings.PAGE_FETCH_ENABLED", True)
    monkeypatch.setattr(
        "app.services.page_enrichment_service.page_fetch_service.fetch",
        lambda url: PageFetchResult(
            status="fetched",
            requested_url=url,
            final_url="https://publisher.example.org/pegasus-review",
            robots_allowed=True,
            http_status=200,
            document=ExtractedDocument(
                canonical_url="https://publisher.example.org/pegasus-review",
                title="Nike Pegasus evidence review",
                main_text="Nike Pegasus is comfortable, but the outsole wears quickly after repeated runs.",
                publisher="Runner Evidence",
                author="A Reviewer",
                source_type="product_review",
                language="en",
                product_data={"name": "Nike Pegasus", "rating_value": 4.2, "review_count": 45},
            ),
        ),
    )

    collection_service.run_pipeline(db_session, brand_id=1, source="google_search")

    post = db_session.query(Post).filter_by(external_id="google-original-page-1").one()
    document = db_session.query(Document).filter_by(post_id=post.id).one()
    snapshot = db_session.query(DocumentSnapshot).filter_by(document_id=document.id).one()
    assert post.url == "https://publisher.example.org/pegasus-review"
    assert "outsole wears quickly" in post.content
    assert document.content_status == "fetched"
    assert document.source_type == "product_review"
    assert snapshot.extracted_data["product_data"]["rating_value"] == 4.2
    assert snapshot.content_text == post.content
