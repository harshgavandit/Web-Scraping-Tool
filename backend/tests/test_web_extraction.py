import socket
from unittest.mock import MagicMock, patch

from app.extraction.page_extractor import extract_public_document
from app.services.page_fetch_service import PageFetchService, is_public_http_url


ARTICLE_HTML = """
<html><head>
  <title>Nike Pegasus 41 long-term review</title>
  <link rel="canonical" href="https://reviews.example.com/nike-pegasus-41" />
  <meta property="og:site_name" content="Runner Reviews" />
  <meta name="author" content="Alex Runner" />
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "Product",
    "name": "Nike Pegasus 41",
    "sku": "FD2722",
    "aggregateRating": {"@type": "AggregateRating", "ratingValue": "4.4", "reviewCount": "128"},
    "review": {"@type": "Review", "reviewBody": "Comfortable but the outsole wears quickly."}
  }
  </script>
</head><body>
  <nav>Navigation that should not be evidence</nav>
  <article>
    <h1>Nike Pegasus 41 long-term review</h1>
    <p>The Pegasus 41 feels comfortable for daily running.</p>
    <p>However, the outsole started wearing after 100 miles.</p>
  </article>
  <footer>Footer links</footer>
</body></html>
"""


def test_article_extractor_preserves_main_evidence_and_product_review_data():
    document = extract_public_document(
        ARTICLE_HTML,
        "https://reviews.example.com/tracking-url",
    )

    assert document.canonical_url == "https://reviews.example.com/nike-pegasus-41"
    assert document.title == "Nike Pegasus 41 long-term review"
    assert document.publisher == "Runner Reviews"
    assert document.author == "Alex Runner"
    assert "comfortable for daily running" in document.main_text
    assert "Navigation that should not be evidence" not in document.main_text
    assert document.source_type == "product_review"
    assert document.product_data["name"] == "Nike Pegasus 41"
    assert document.product_data["rating_value"] == 4.4
    assert document.product_data["review_count"] == 128


def test_article_extractor_accepts_json_ld_type_arrays_from_live_publishers():
    html = """
    <html><head>
      <link rel="canonical" href="https://publisher.example.test/nike-story" />
      <script type="application/ld+json">
      {"@context":"https://schema.org", "@type":["NewsArticle", "Thing"],
       "headline":"Nike story", "datePublished":"2026-09-18T10:00:00Z"}
      </script>
    </head><body><article><p>Nike has published a verified story.</p></article></body></html>
    """

    document = extract_public_document(html, "https://publisher.example.test/tracking")

    assert document.canonical_url == "https://publisher.example.test/nike-story"
    assert document.title == "Nike story"
    assert document.source_type == "news"


def test_public_url_guard_rejects_private_and_loopback_targets():
    private_answer = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 0))]
    public_answer = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))]

    assert is_public_http_url("http://localhost/admin", resolver=lambda *_: private_answer) is False
    assert is_public_http_url("http://127.0.0.1/admin", resolver=lambda *_: private_answer) is False
    assert is_public_http_url("https://reviews.example.com/nike", resolver=lambda *_: public_answer) is True
    assert is_public_http_url("file:///etc/passwd", resolver=lambda *_: public_answer) is False


def test_page_fetcher_honors_robots_and_never_requests_disallowed_page():
    service = PageFetchService(resolver=lambda *_: [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0)),
    ])
    robots = MagicMock(status_code=200, text="User-agent: *\nDisallow: /private", headers={})

    with patch("httpx.Client.get", return_value=robots) as get:
        result = service.fetch("https://reviews.example.com/private/nike")

    assert result.status == "blocked"
    assert result.robots_allowed is False
    assert get.call_count == 1


def test_page_fetcher_returns_original_extracted_page_with_final_url():
    service = PageFetchService(resolver=lambda *_: [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0)),
    ])
    robots = MagicMock(status_code=404, text="", headers={})
    page = MagicMock(
        status_code=200,
        text=ARTICLE_HTML,
        headers={"content-type": "text/html; charset=utf-8"},
        url="https://reviews.example.com/nike-pegasus-41",
    )

    with patch("httpx.Client.get", side_effect=[robots, page]):
        result = service.fetch("https://google.example/redirect")

    assert result.status == "fetched"
    assert result.document.canonical_url == "https://reviews.example.com/nike-pegasus-41"
    assert "outsole started wearing" in result.document.main_text


def test_page_fetcher_revalidates_redirect_before_requesting_target():
    public_answer = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))]
    private_answer = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 0))]

    def resolver(hostname, *_):
        return private_answer if hostname == "127.0.0.1" else public_answer

    service = PageFetchService(resolver=resolver)
    robots = MagicMock(status_code=404, text="", headers={}, url="https://reviews.example.com/robots.txt")
    redirect = MagicMock(
        status_code=302,
        text="",
        headers={"location": "http://127.0.0.1/internal"},
        url="https://reviews.example.com/nike",
    )

    with patch("httpx.Client.get", side_effect=[robots, redirect]) as get:
        result = service.fetch("https://reviews.example.com/nike")

    assert result.status == "blocked"
    assert "redirect" in result.error.lower()
    assert get.call_count == 2
