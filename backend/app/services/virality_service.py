import math
from datetime import datetime
from typing import Tuple, Optional
from app.core.config import settings
from app.utils.datetime_utils import utc_now

"""
Virality Scoring Documentation:
------------------------------
The virality algorithm prioritizes momentum and engagement velocity over stale, cumulative likes.

Formula Components:
1. Weighted Engagement:
   engagement = safe_likes + (safe_comments * 2.5) + (safe_shares * 3.5)
   Comments and shares indicate high active discussion and amplification compared to passive likes.

2. Time Decay & Velocity:
   age_hours = max((now - published_at).total_seconds() / 3600.0, 0.5)
   velocity = engagement / age_hours

3. Composite Virality Score (0 - 100):
   - Velocity component (up to 70 pts): exponential decay curve responsive to velocity
   - Volume component (up to 30 pts): log response to absolute engagement
   Score = min(100.0, round((velocity_points * 0.70) + (volume_points * 0.30), 1))

4. Levels:
   0  - 39: Low
   40 - 64: Medium
   65 - 84: High
   85 - 100: Viral (is_viral = True)
"""

LEVEL_LOW = "Low"
LEVEL_MEDIUM = "Medium"
LEVEL_HIGH = "High"
LEVEL_VIRAL = "Viral"


def calculate_engagement_and_virality(
    likes: Optional[int] = 0,
    comments: Optional[int] = 0,
    shares: Optional[int] = 0,
    published_at: Optional[datetime] = None,
    now: Optional[datetime] = None,
    source: str = "generic",
    viral_threshold: Optional[int] = None
) -> Tuple[int, float, float, str, bool]:
    """
    Computes:
      - engagement_count (int)
      - engagement_velocity (float)
      - virality_score (float 0.0 - 100.0)
      - virality_level (str)
      - is_viral (bool)

    Gracefully handles None, negative, missing, or future timestamps.
    """
    if now is None:
        now = utc_now()

    # Safely coerce missing, None, or negative engagement values to 0
    safe_likes = max(0, int(likes or 0))
    safe_comments = max(0, int(comments or 0))
    safe_shares = max(0, int(shares or 0))

    # 1. Weighted engagement
    raw_engagement = (safe_likes * 1.0) + (safe_comments * 2.5) + (safe_shares * 3.5)
    engagement_count = int(round(raw_engagement))

    # 2. Safe velocity computation with clock-skew protection
    if published_at:
        # Strip tzinfo if any for comparison with utc_now()
        pub_naive = published_at.replace(tzinfo=None) if published_at.tzinfo else published_at
        diff_seconds = max((now - pub_naive).total_seconds(), 60.0)
        age_hours = max(diff_seconds / 3600.0, 0.5)
    else:
        age_hours = 24.0

    velocity = round(raw_engagement / age_hours, 2)

    # 3. Source baseline adjustment
    scale_divisor = 50.0
    if source in ("reddit", "facebook"):
        scale_divisor = 100.0

    # 4. Velocity score component (0 to 100)
    vel_score = 100.0 * (1.0 - math.exp(-velocity / scale_divisor))

    # Volume score component (0 to 100)
    vol_score = 0.0
    if raw_engagement > 0:
        vol_score = min(100.0, 20.0 * math.log10(raw_engagement + 1))

    # Composite score
    composite = (vel_score * 0.70) + (vol_score * 0.30)
    if math.isnan(composite) or math.isinf(composite):
        virality_score = 0.0
    else:
        virality_score = round(min(max(composite, 0.0), 100.0), 1)

    threshold = viral_threshold if viral_threshold is not None else settings.VIRAL_THRESHOLD

    # Determine Virality Level
    if virality_score >= threshold:
        virality_level = LEVEL_VIRAL
        is_viral = True
    elif virality_score >= 65.0:
        virality_level = LEVEL_HIGH
        is_viral = False
    elif virality_score >= 40.0:
        virality_level = LEVEL_MEDIUM
        is_viral = False
    else:
        virality_level = LEVEL_LOW
        is_viral = False

    return engagement_count, velocity, virality_score, virality_level, is_viral
