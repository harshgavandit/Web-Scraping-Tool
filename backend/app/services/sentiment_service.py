import re
from typing import Dict, Any, Tuple
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer = SentimentIntensityAnalyzer()

# Contrastive indicators that frequently signal mixed sentiment or nuanced caveats
MIXED_INDICATORS = [
    r"\bbut\b", r"\bhowever\b", r"\byet\b", r"\balthough\b",
    r"\bthough\b", r"\bon the other hand\b", r"\bexcept\b",
    r"\bdespite\b", r"\beven though\b"
]

NEGATIVE_CONSUMER_CUES = [
    r"\bexpensive\b", r"\boverpriced\b", r"\bpricey\b", r"\bsteep\b",
    r"\bcostly\b", r"\bcheaply made\b", r"\bbroke\b", r"\btears\b",
    r"\bsqueak\b", r"\bhurts\b", r"\bblister\b", r"\bcramped\b",
    r"\bdisappointing\b", r"\bflawed\b", r"\blacks\b", r"\btoo high\b"
]

POSITIVE_CONSUMER_CUES = [
    r"\bcomfortable\b", r"\bcomfort\b", r"\blove\b", r"\bgreat\b",
    r"\bamazing\b", r"\bspringy\b", r"\bcushion\b", r"\bresponsive\b",
    r"\bbeautiful\b", r"\bfavorite\b", r"\bperfect\b", r"\bexcellent\b"
]


def analyze_local_sentiment(text: str) -> Tuple[str, float, bool]:
    """
    Analyzes sentiment using free local VADER with consumer domain enhancements.
    Returns:
      (sentiment_label: str, sentiment_score: float, needs_deeper_ai: bool)
      sentiment_label is one of: Positive, Negative, Neutral, Mixed.
      sentiment_score is compound score between -1.0 and 1.0.
      needs_deeper_ai is True when ambiguity, sarcasm, or mixed complexity warrants Gemini analysis.
    """
    if not text or not text.strip():
        return "Neutral", 0.0, False

    scores: Dict[str, float] = _analyzer.polarity_scores(text)
    compound: float = scores["compound"]
    pos: float = scores["pos"]
    neg: float = scores["neg"]
    neu: float = scores["neu"]

    lower_text = text.lower()
    has_contrast = any(re.search(pat, lower_text) for pat in MIXED_INDICATORS)
    has_pos_cue = any(re.search(pat, lower_text) for pat in POSITIVE_CONSUMER_CUES)
    has_neg_cue = any(re.search(pat, lower_text) for pat in NEGATIVE_CONSUMER_CUES)

    # Mixed detection:
    # 1. Significant VADER positive and negative signals present
    # 2. Contrast indicator combined with positive and negative consumer cues (e.g., "comfortable but expensive")
    if (pos >= 0.12 and neg >= 0.12) or (has_contrast and has_pos_cue and has_neg_cue):
        sentiment = "Mixed"
        needs_ai = True
    elif (has_contrast and pos >= 0.08 and neg >= 0.08):
        sentiment = "Mixed"
        needs_ai = True
    elif compound >= 0.05:
        # Check if negative consumer cue tempers the score
        if has_neg_cue and has_contrast:
            sentiment = "Mixed"
            needs_ai = True
        else:
            sentiment = "Positive"
            needs_ai = compound < 0.25 and has_contrast
    elif compound <= -0.05:
        if has_pos_cue and has_contrast:
            sentiment = "Mixed"
            needs_ai = True
        else:
            sentiment = "Negative"
            needs_ai = compound > -0.25 and has_contrast
    else:
        # Neutral compound score
        if has_pos_cue and has_neg_cue:
            sentiment = "Mixed"
            needs_ai = True
        elif has_pos_cue:
            sentiment = "Positive"
            needs_ai = False
        elif has_neg_cue:
            sentiment = "Negative"
            needs_ai = False
        else:
            sentiment = "Neutral"
            needs_ai = len(text) > 80 and neu > 0.85

    return sentiment, round(compound, 3), needs_ai
