from app.collectors.mock import MockCollector
from app.collectors.reddit import RedditCollector
from app.collectors.facebook import FacebookCollector
from app.collectors.rss import RSSCollector
from app.services.collection_service import collection_service
from app.collectors.base import BaseCollector, RawPost
from app.models.post import Post
from app.models.post_analysis import PostAnalysis
from app.schemas.post_analysis import AIAnalysisItem
from app.utils.datetime_utils import utc_now
from unittest.mock import MagicMock, patch


def test_mock_collector():
    collector = MockCollector()
    assert collector.is_enabled() is True
    posts = collector.collect("Nike", ["Nike shoes"], ["Adidas"], limit=10)
    assert len(posts) == 10
    assert posts[0].content is not None
    assert posts[0].likes >= 0


def test_reddit_collector_graceful_fallback():
    collector = RedditCollector()
    # Without credentials, collect should not raise error and returns mock reddit posts
    posts = collector.collect("Nike", ["Nike"], ["Adidas"], limit=5)
    assert len(posts) > 0
    assert all(p.source == "reddit" for p in posts)


def test_facebook_collector_graceful_fallback():
    collector = FacebookCollector()
    posts = collector.collect("Nike", ["Nike"], ["Adidas"], limit=5)
    assert len(posts) > 0
    assert all(p.source == "facebook" for p in posts)


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


def test_collection_pipeline_resilience(db_session):
    # Running pipeline with mock collectors shouldn't raise exception
    runs = collection_service.run_pipeline(db=db_session, brand_id=1, source="mock", limit_per_source=5)
    assert len(runs) >= 1
    assert runs[0].status == "completed"
    assert runs[0].records_found >= 1


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
