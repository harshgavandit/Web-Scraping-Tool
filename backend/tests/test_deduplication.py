from app.services.deduplication_service import (
    normalize_text, compute_content_hash, canonicalize_url, is_duplicate_post
)
from app.models.post import Post


def test_normalize_text():
    raw = "  Nike   Air   MAX   is   Awesome!  \n\n  "
    expected = "nike air max is awesome!"
    assert normalize_text(raw) == expected


def test_content_hash_consistency():
    t1 = "Love my new Nike Pegasus shoes!"
    t2 = "love my   new nike pegasus shoes!  "
    t3 = "LOVE MY NEW NIKE PEGASUS SHOES!\n\n"
    assert compute_content_hash(t1) == compute_content_hash(t2)
    assert compute_content_hash(t1) == compute_content_hash(t3)


def test_canonicalize_url():
    dirty_url = "https://reddit.com/r/sneakers/post_123/?utm_source=twitter&utm_medium=social&fbclid=abc123xyz"
    clean_url = canonicalize_url(dirty_url)
    assert "utm_source" not in clean_url
    assert "fbclid" not in clean_url
    assert clean_url == "https://reddit.com/r/sneakers/post_123"


def test_canonicalize_url_strips_various_tracking_params():
    url = "https://example.com/nike-air-max/?utm_campaign=summer_sale&utm_term=kicks&ref=homepage&igshid=xyz987"
    clean = canonicalize_url(url)
    assert clean == "https://example.com/nike-air-max"


def test_canonicalize_url_rejects_unsafe_schemes():
    assert canonicalize_url("javascript:alert(1)") is None
    assert canonicalize_url("data:text/html,<script>alert(1)</script>") is None


def test_duplicate_detection(db_session):
    original_content = "Great running shoes by Nike with unmatched comfort"
    p = Post(
        brand_id=1,
        source="reddit",
        external_id="t3_12345",
        url="https://reddit.com/r/sneakers/comments/12345",
        content=original_content,
        content_hash=compute_content_hash(original_content)
    )
    db_session.add(p)
    db_session.commit()

    # 1. Matches external_id
    assert is_duplicate_post(db_session, "reddit", "t3_12345", "different_hash") is True

    # 2. Matches exact content_hash
    assert is_duplicate_post(db_session, "twitter", "new_id", compute_content_hash(original_content)) is True

    # 3. Matches content with different casing & whitespaces
    variation = "  GREAT   running SHOES by Nike with unmatched comfort \n\n"
    assert is_duplicate_post(db_session, "web", "new_id_2", compute_content_hash(variation)) is True

    # 4. Matches canonical URL with tracking parameters
    dup_url = "https://reddit.com/r/sneakers/comments/12345?utm_source=reddit_app&fbclid=123"
    assert is_duplicate_post(db_session, "news", "id_3", "unique_hash", url=dup_url) is True

    # 5. New unique post
    assert is_duplicate_post(db_session, "reddit", "t3_99999", compute_content_hash("Completely unique post")) is False
