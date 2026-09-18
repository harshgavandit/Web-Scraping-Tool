import math
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple

from app.utils.datetime_utils import utc_now


@dataclass(frozen=True)
class AspectEvidence:
    aspect: str
    sentiment: str
    score: float
    quote: str
    confidence: float


ASPECT_PATTERNS = {
    "Comfort": r"\b(comfort|comfortable|cushion|cushioning|soft|harsh|uncomfortable|hurts?|confort|cómod[oa]|bequem|comodità|agréable)\b",
    "Fit & Sizing": r"\b(fit|fits|sizing|size|narrow|wide|tight|loose|true to size|talla|taille|größe|tamanho|ajusté|apretad[oa]|estrech[oa]|serré|eng)\b",
    "Stability": r"\b(stable|stability|support|supportive|wobbly|estabilidad|stabilité|stabilität|sostenut[oa])\b",
    "Durability": r"\b(durability|durable|outsole|wore out|wears? out|broke|broken|tear|torn|sole separation|durabilidad|durabilité|haltbar|suela|semelle|sohle|desgastad[oa]|déchiré|kaputt)\b",
    "Price & Value": r"\b(price|pricing|expensive|overpriced|cheap|affordable|value|cost|precio|prix|preis|car[oa]|cher|teuer|barat[oa]|bon marché|billig|custo)\b",
    "Performance": r"\b(performance|responsive|speed|fast|energy return|race|running|rendimiento|performant|leistung|schnell|vitesse|velocidad)\b",
    "Style & Design": r"\b(style|design|colorway|looks?|aesthetic|fashion|diseño|stil|estétic[oa]|beau|schön|bonit[oa])\b",
    "Customer Experience": r"\b(customer service|shipping|delivery|refund|return|order|checkout|snkrs|servicio al cliente|service client|kundenservice|entrega|livraison|versand|devolución|retour)\b",
    "Sustainability": r"\b(sustainable|sustainability|recycled|environment|eco-friendly|sostenible|nachhaltig|sustentável)\b",
}

POSITIVE = re.compile(
    r"\b(love|excellent|great|best|comfortable|stable|durable|affordable|responsive|beautiful|recommend|"
    r"excelente|buen[oa]|genial|parfait|super|toll|wunderbar|ótim[oa]|fantastique|incredibile|confortable)\b",
    re.I,
)
NEGATIVE = re.compile(
    r"\b(hate|poor|bad|worst|uncomfortable|wore out|wears? out|broke|broken|expensive|overpriced|problem|complaint|delayed|frustrating|"
    r"mal[oa]|pésim[oa]|terrible|déçu|mauvais|schlimm|fehler|frustrante|deficiente|cher|teuer|inconfortable|car[oa])\b",
    re.I,
)


def resolve_product(text: str, products: Iterable[Dict[str, Any]]) -> Optional[str]:
    for product in products:
        names = [product.get("name"), *(product.get("aliases") or [])]
        for name in sorted((name for name in names if name), key=len, reverse=True):
            if re.search(rf"(?<!\w){re.escape(name)}(?!\w)", text, re.I):
                return product.get("name")
    return None


def extract_aspect_evidence(text: str) -> List[AspectEvidence]:
    sentences = [
        part.strip()
        for part in re.split(r"(?<=[.!?])\s+|\n+|,\s*(?:but|however|mais|pero|aber)\s+", text, flags=re.I)
        if part.strip()
    ]
    evidence: List[AspectEvidence] = []
    for sentence in sentences:
        positive_count = len(POSITIVE.findall(sentence))
        negative_count = len(NEGATIVE.findall(sentence))
        if positive_count > negative_count:
            sentiment, score = "Positive", min(1.0, 0.35 + positive_count * 0.2)
        elif negative_count > positive_count:
            sentiment, score = "Negative", max(-1.0, -0.35 - negative_count * 0.2)
        elif positive_count and negative_count:
            sentiment, score = "Mixed", 0.0
        else:
            sentiment, score = "Neutral", 0.0
        for aspect, pattern in ASPECT_PATTERNS.items():
            if re.search(pattern, sentence, re.I):
                evidence.append(AspectEvidence(
                    aspect=aspect,
                    sentiment=sentiment,
                    score=round(score, 2),
                    quote=sentence[:500],
                    confidence=0.9 if sentiment != "Neutral" else 0.7,
                ))
    return evidence


def calculate_attention_score(
    published_at: Optional[datetime],
    search_position: Optional[int],
    review_count: Optional[int],
    now: Optional[datetime] = None,
) -> Tuple[float, str, List[str]]:
    now = now or utc_now()
    reasons: List[str] = []
    recency = 0.0
    if published_at:
        age_hours = max(0.0, (now - published_at.replace(tzinfo=None)).total_seconds() / 3600)
        if age_hours <= 24:
            recency = 40.0
            reasons.append("published in the last 24 hours")
        elif age_hours <= 24 * 7:
            recency = 32.0
            reasons.append("published in the last 7 days")
        elif age_hours <= 24 * 30:
            recency = 20.0
            reasons.append("published in the last 30 days")
        elif age_hours <= 24 * 90:
            recency = 10.0

    visibility = 0.0
    if search_position is not None:
        if search_position <= 3:
            visibility = 30.0
            reasons.append("top 3 Google result")
        elif search_position <= 10:
            visibility = 22.0
            reasons.append("first-page Google result")
        elif search_position <= 20:
            visibility = 12.0

    review_signal = 0.0
    if review_count and review_count > 0:
        review_signal = min(30.0, 10.0 * math.log10(review_count + 1))
        reasons.append(f"{review_count} published reviews")

    score = round(min(100.0, recency + visibility + review_signal), 1)
    level = "Surging" if score >= 85 else "High attention" if score >= 65 else "Growing" if score >= 40 else "Emerging" if score >= 20 else "Low attention"
    return score, level, reasons


def calculate_reputation_risk(
    negative_mentions: int,
    unique_sources: int,
    growth_pct: float,
    average_confidence: float,
) -> Tuple[float, str]:
    if negative_mentions <= 0:
        return 0.0, "Monitor"
    score = (
        min(40.0, negative_mentions * 2.4)
        + min(25.0, unique_sources * 5.0)
        + min(20.0, max(0.0, growth_pct) / 4.0)
        + min(10.0, max(0.0, average_confidence) * 10.0)
    )
    score = round(min(100.0, score), 0)
    level = "Critical" if score >= 75 else "Elevated" if score >= 50 else "Emerging" if score >= 25 else "Monitor"
    return score, level
