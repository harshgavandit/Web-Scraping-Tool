import re
from typing import List, Tuple, Optional

# Irrelevant context terms that indicate homonym noise (e.g., Greek mythology, missile defense)
IRRELEVANT_CONTEXT_PATTERNS = [
    r"\bgoddess of victory\b",
    r"\bgreek mythology\b",
    r"\bnike missile\b",
    r"\bproject nike\b",
    r"\bwinged victory of samothrace\b",
]

# High-confidence footwear/apparel context cues
RELEVANT_CONTEXT_CUES = [
    "shoe", "shoes", "sneaker", "sneakers", "kicks", "runner", "running",
    "dunk", "jordan", "air max", "pegasus", "cleats", "jersey", "hoodie",
    "apparel", "sizing", "cushion", "midsole", "outsole", "fit", "order",
    "shipping", "return", "snkrs", "snkrs app", "retail", "drop", "restock",
    "price", "pricing", "expensive", "comfortable", "comfort", "quality", "durability",
    "customer service", "adidas", "puma", "new balance", "under armour"
]


def evaluate_relevance(
    text: str,
    brand_keywords: List[str],
    product_names: List[str],
    competitors: List[str]
) -> Tuple[bool, float, Optional[str]]:
    """
    Evaluates whether a social post is truly relevant to brand chatter.
    Returns: (is_relevant: bool, relevance_score: float, matched_entity: Optional[str])
    """
    if not text:
        return False, 0.0, None

    lower_text = text.lower()

    # 1. Check for negative/irrelevant homonym context
    for pattern in IRRELEVANT_CONTEXT_PATTERNS:
        if re.search(pattern, lower_text):
            return False, 0.1, None

    score = 0.0
    matched_entity = None

    # 2. Check brand keywords
    for kw in brand_keywords:
        if re.search(r"\b" + re.escape(kw.lower()) + r"\b", lower_text):
            score += 0.4
            if not matched_entity:
                matched_entity = kw

    # 3. Check product mentions
    for prod in product_names:
        if re.search(r"\b" + re.escape(prod.lower()) + r"\b", lower_text):
            score += 0.4
            matched_entity = prod

    # 4. Check competitor mentions
    for comp in competitors:
        if re.search(r"\b" + re.escape(comp.lower()) + r"\b", lower_text):
            score += 0.3
            if not matched_entity:
                matched_entity = comp

    # 5. Check relevant retail/apparel/sneaker context cues
    cue_matches = sum(1 for cue in RELEVANT_CONTEXT_CUES if cue in lower_text)
    if cue_matches > 0:
        score += min(cue_matches * 0.15, 0.4)

    # A post is relevant if score >= 0.4
    is_relevant = score >= 0.4
    return is_relevant, round(min(score, 1.0), 2), matched_entity
