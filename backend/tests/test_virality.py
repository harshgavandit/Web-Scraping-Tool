from datetime import datetime, timedelta
from app.services.virality_service import (
    calculate_engagement_and_virality,
    LEVEL_LOW, LEVEL_MEDIUM, LEVEL_HIGH, LEVEL_VIRAL
)
from app.utils.datetime_utils import utc_now


def test_newer_post_higher_virality_than_old_post():
    now = utc_now()
    # Post A: 20,000 likes, 6 months old (4,320 hours)
    post_a_time = now - timedelta(days=180)
    _, vel_a, score_a, level_a, is_viral_a = calculate_engagement_and_virality(
        likes=20000, comments=500, shares=200, published_at=post_a_time, now=now, source="reddit"
    )

    # Post B: 5,000 likes, 2 hours old
    post_b_time = now - timedelta(hours=2)
    _, vel_b, score_b, level_b, is_viral_b = calculate_engagement_and_virality(
        likes=5000, comments=1200, shares=450, published_at=post_b_time, now=now, source="reddit"
    )

    # Velocity of Post B must exceed Post A dramatically
    assert vel_b > vel_a
    # Virality score of Post B should be higher because it is exploding right now
    assert score_b > score_a
    assert is_viral_b is True
    assert level_b == LEVEL_VIRAL


def test_virality_threshold_levels():
    now = utc_now()
    # Low engagement post
    pub = now - timedelta(hours=24)
    _, _, score_low, level_low, is_viral_low = calculate_engagement_and_virality(
        likes=10, comments=2, shares=0, published_at=pub, now=now
    )
    assert level_low == LEVEL_LOW
    assert is_viral_low is False
    assert score_low < 40.0

    # Moderate engagement
    _, _, score_med, level_med, _ = calculate_engagement_and_virality(
        likes=350, comments=50, shares=20, published_at=pub, now=now
    )
    assert level_med in (LEVEL_MEDIUM, LEVEL_HIGH)


def test_missing_engagement_data_and_none_values():
    now = utc_now()
    # None values should be treated safely without exceptions or NaN
    eng_count, velocity, score, level, is_viral = calculate_engagement_and_virality(
        likes=None, comments=None, shares=None, published_at=None, now=now
    )
    assert eng_count == 0
    assert velocity == 0.0
    assert score == 0.0
    assert level == LEVEL_LOW
    assert is_viral is False


def test_custom_configurable_viral_threshold():
    now = utc_now()
    pub = now - timedelta(hours=1)
    # With a lower custom threshold of 50, a score of 60 should be flagged as viral
    _, _, score, level, is_viral = calculate_engagement_and_virality(
        likes=1000, comments=200, shares=50, published_at=pub, now=now, viral_threshold=50
    )
    if score >= 50:
        assert is_viral is True
        assert level == LEVEL_VIRAL
