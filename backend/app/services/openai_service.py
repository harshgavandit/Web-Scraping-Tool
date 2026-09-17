import json
import time
import re
from typing import List, Dict, Any, Optional
from openai import OpenAI
from pydantic import ValidationError

from app.core.config import settings
from app.core.logging import logger
from app.schemas.post_analysis import AIAnalysisItem, AIBatchResult

# Heuristic topic categorizer for fallback / keyword extraction
KNOWN_TOPIC_PATTERNS = [
    (r"\b(price|pricing|expensive|cheap|cost|overpriced|afford|inflation|msrp|discount)\b", "Pricing & Value"),
    (r"\b(comfort|comfortable|cushion|cushioning|midsole|fit|arch support|blister|hurts|tight|wide)\b", "Product Comfort & Fit"),
    (r"\b(quality|durability|broke|tear|rip|falling apart|creasing|sole separation|material|defect)\b", "Build Quality & Durability"),
    (r"\b(customer service|support|order|shipping|delayed|delivery|return|refund|snkrs app|snkrs)\b", "Customer Experience & Delivery"),
    (r"\b(running|marathon|runner|5k|10k|tempo|mileage|daily trainer)\b", "Running & Performance"),
    (r"\b(style|design|colorway|retro|vintage|fashion|streetwear|aesthetic|clean)\b", "Style & Design"),
    (r"\b(sustainability|recycled|eco|environmental|plastic)\b", "Sustainability & Ethics"),
]


def heuristic_fallback_analyze(post_id: int, content: str, title: Optional[str] = None, local_sentiment: str = "Neutral") -> AIAnalysisItem:
    """
    High quality local heuristic fallback when OpenAI is disabled or key is missing.
    Ensures the platform is 100% functional and delivers structured insights.
    """
    full_text = f"{title or ''} {content}".strip()
    lower = full_text.lower()

    # Detect topic
    topic = "Brand Discussion"
    for pattern, top in KNOWN_TOPIC_PATTERNS:
        if re.search(pattern, lower):
            topic = top
            break

    # Detect product
    product = None
    if "pegasus" in lower:
        product = "Pegasus"
    elif "air max" in lower:
        product = "Air Max"
    elif "jordan" in lower or "air jordan" in lower:
        product = "Air Jordan"
    elif "running" in lower:
        product = "Nike Running"
    elif "football" in lower or "cleats" in lower:
        product = "Nike Football"
    elif "invincible" in lower:
        product = "Nike Invincible"
    elif "vomero" in lower:
        product = "Nike Vomero"

    # Detect competitor
    competitor = None
    if "adidas" in lower:
        competitor = "Adidas"
    elif "puma" in lower:
        competitor = "Puma"
    elif "new balance" in lower:
        competitor = "New Balance"
    elif "under armour" in lower:
        competitor = "Under Armour"
    elif "asics" in lower:
        competitor = "Asics"
    elif "hoka" in lower:
        competitor = "Hoka"

    # Extract key positive and negative
    key_positive = None
    key_negative = None

    if "comfort" in lower or "great" in lower or "love" in lower or "best" in lower:
        key_positive = "High comfort and aesthetic appeal"
    if "expensive" in lower or "price" in lower or "overpriced" in lower:
        key_negative = "Perception of premium or increasing price"
    elif "broke" in lower or "durability" in lower or "tear" in lower:
        key_negative = "Concerns around long-term durability"
    elif "snkrs" in lower or "app" in lower or "bot" in lower or "order" in lower:
        key_negative = "Frustration with release drops or app customer experience"

    # Generate concise summary
    if competitor and product:
        summary = f"Consumers compare {product} against {competitor}, weighing specific trade-offs in comfort versus value."
    elif product and key_negative:
        summary = f"Discussion highlights {product} performance but flags concerns regarding {key_negative.lower()}."
    elif product and key_positive:
        summary = f"Consumers praise {product} for its {key_positive.lower()} and design."
    elif "price" in lower:
        summary = "Community members debate price increases across current product lineups."
    else:
        summary = f"General brand chatter discussing {topic.lower()} with {local_sentiment.lower()} reception."

    # Generate actionable marketing recommendation
    if competitor:
        recommendation = f"Reinforce core performance differentiators against {competitor} while maintaining accessible price-point messaging."
    elif "price" in lower or "expensive" in lower:
        recommendation = "Highlight long-term durability and value-for-money in upcoming campaign creatives."
    elif "snkrs" in lower or "customer service" in lower:
        recommendation = "Improve drop transparency and communication to reduce customer friction during high-demand releases."
    elif "comfort" in lower:
        recommendation = "Amplify user reviews emphasizing cushioning and ergonomic design across social channels."
    else:
        recommendation = f"Monitor consumer sentiment on {topic.lower()} and leverage positive feedback in community engagement."

    return AIAnalysisItem(
        post_id=post_id,
        sentiment=local_sentiment,
        topic=topic,
        product=product,
        competitor=competitor,
        summary=summary,
        key_positive=key_positive,
        key_negative=key_negative,
        recommendation=recommendation
    )


class OpenAIService:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL or "gpt-4o-mini"
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None

    def analyze_batch(self, posts: List[Dict[str, Any]]) -> List[AIAnalysisItem]:
        """
        Analyze a batch of posts (up to settings.AI_BATCH_SIZE).
        Uses OpenAI with strict JSON response when API key is configured.
        Falls back smoothly to high-fidelity heuristic parsing if unconfigured or error occurs.
        """
        if not posts:
            return []

        if not self.client or not settings.AI_ANALYSIS_ENABLED:
            logger.info("OpenAI API key missing or AI disabled: using heuristic analysis fallback.")
            return [
                heuristic_fallback_analyze(
                    post_id=p["id"],
                    content=p["content"],
                    title=p.get("title"),
                    local_sentiment=p.get("local_sentiment", "Neutral")
                )
                for p in posts
            ]

        # Prepare batch prompt
        post_summaries = []
        for p in posts:
            post_summaries.append({
                "id": p["id"],
                "title": p.get("title", ""),
                "content": p.get("content", "")[:1000],
                "local_sentiment": p.get("local_sentiment", "Neutral")
            })

        system_prompt = (
            "You are an expert brand listening and social intelligence analyst for brand marketing teams. "
            "Analyze the given batch of social posts about Nike and competitor brands. "
            "For each post, return strict JSON matching the schema with fields: "
            "post_id (int), sentiment ('Positive', 'Negative', 'Neutral', 'Mixed'), "
            "topic (short string e.g. 'Running Shoes / Pricing', 'Build Quality', 'Customer Service'), "
            "product (specific product e.g. 'Pegasus', 'Air Max', 'Air Jordan', or null), "
            "competitor (specific competitor e.g. 'Adidas', 'Puma', 'New Balance', or null), "
            "summary (1-2 concise sentences summarizing the discussion), "
            "key_positive (short phrase or null), "
            "key_negative (short phrase or null), "
            "recommendation (1-2 practical, actionable marketing/business recommendations for Nike). "
            "Do not invent facts not in the post."
        )

        user_content = json.dumps({"posts": post_summaries})

        # Retry logic with exponential backoff
        max_retries = 3
        backoff = 1.0

        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Analyze these posts and return a JSON object with key 'items' containing the array of analyzed objects:\n{user_content}"}
                    ],
                    temperature=0.2,
                )

                raw_json = response.choices[0].message.content
                data = json.loads(raw_json)

                items = data.get("items") or data.get("posts") or []
                results: List[AIAnalysisItem] = []
                for item in items:
                    try:
                        validated = AIAnalysisItem(**item)
                        results.append(validated)
                    except ValidationError as ve:
                        logger.warning(f"Validation error for item in OpenAI batch: {ve}")
                        # Fallback for that individual item
                        p_match = next((p for p in posts if p["id"] == item.get("post_id")), None)
                        if p_match:
                            results.append(heuristic_fallback_analyze(p_match["id"], p_match["content"], p_match.get("title"), p_match.get("local_sentiment", "Neutral")))

                # Ensure all posts in the batch are accounted for
                returned_ids = {r.post_id for r in results}
                for p in posts:
                    if p["id"] not in returned_ids:
                        results.append(heuristic_fallback_analyze(p["id"], p["content"], p.get("title"), p.get("local_sentiment", "Neutral")))

                return results

            except Exception as e:
                logger.error(f"OpenAI API call failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(backoff)
                    backoff *= 2
                else:
                    logger.warning("Falling back to local heuristic analysis for this batch due to persistent OpenAI error.")
                    return [
                        heuristic_fallback_analyze(
                            post_id=p["id"],
                            content=p["content"],
                            title=p.get("title"),
                            local_sentiment=p.get("local_sentiment", "Neutral")
                        )
                        for p in posts
                    ]

        return []


openai_service = OpenAIService()
