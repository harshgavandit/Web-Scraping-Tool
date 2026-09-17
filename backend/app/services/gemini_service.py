import json
import time
from typing import List, Dict, Any, Optional
import httpx
from pydantic import ValidationError

from app.core.config import settings
from app.core.logging import logger
from app.schemas.post_analysis import AIAnalysisItem
from app.services.openai_service import heuristic_fallback_analyze


class GeminiService:
    """
    Service client for Google Gemini 3.8 Flash (and configured Gemini models).
    Communicates via Google's Gemini REST API with structured JSON output and low-latency batching.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key if api_key is not None else settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL or "gemini-3.8-flash"
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    def analyze_batch(
        self,
        posts: List[Dict[str, Any]],
        strong_reasoning: bool = False
    ) -> List[AIAnalysisItem]:
        """
        Analyze a batch of posts using Gemini 3.8 Flash with structured JSON output.
        Falls back to local heuristic analysis when API key is unset, disabled, or if API fails.
        """
        if not posts:
            return []

        # Graceful local fallback when key is absent or AI is disabled
        if not self.api_key or not settings.AI_ANALYSIS_ENABLED:
            logger.info("Gemini API key missing or AI analysis disabled: using local heuristic fallback.")
            return [
                heuristic_fallback_analyze(
                    post_id=p["id"],
                    content=p["content"],
                    title=p.get("title"),
                    local_sentiment=p.get("local_sentiment", "Neutral")
                )
                for p in posts
            ]

        post_summaries = []
        for p in posts:
            post_summaries.append({
                "id": p["id"],
                "title": p.get("title", ""),
                "content": p.get("content", "")[:1000],
                "local_sentiment": p.get("local_sentiment", "Neutral")
            })

        system_instruction = (
            "You are an expert brand listening and social intelligence analyst for brand marketing teams. "
            "Analyze the given batch of social posts about Nike and competitor brands. "
            "For each post, return strict JSON matching the schema with fields: "
            "post_id (int), sentiment (copy the supplied local_sentiment exactly; do not reclassify it), "
            "topic (short string e.g. 'Running & Performance', 'Product Comfort & Fit', 'Pricing & Value', 'Build Quality & Durability', 'Customer Experience & Delivery', 'Style & Design', 'Sustainability & Ethics'), "
            "product (specific product e.g. 'Pegasus', 'Air Max', 'Air Jordan', 'Nike Running', or null), "
            "competitor (specific competitor e.g. 'Adidas', 'Puma', 'New Balance', 'Under Armour', or null), "
            "summary (1-2 concise sentences summarizing the discussion), "
            "key_positive (short phrase or null), "
            "key_negative (short phrase or null), "
            "recommendation (1-2 practical, actionable marketing/business recommendations for Nike). "
            "Do not invent facts not in the post."
        )

        user_content = (
            f"{system_instruction}\n\n"
            f"Analyze these posts and return a JSON object with key 'items' containing the array of analyzed objects:\n"
            f"{json.dumps({'posts': post_summaries})}"
        )

        url = f"{self.base_url}/models/{self.model}:generateContent"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }

        # Prefer low reasoning/thinking for routine bulk analysis
        generation_config: Dict[str, Any] = {
            "temperature": 0.2,
            "responseMimeType": "application/json"
        }
        if not strong_reasoning:
            generation_config["thinkingConfig"] = {"thinkingBudget": 0}

        payload: Dict[str, Any] = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_content}]
                }
            ],
            "generationConfig": generation_config
        }

        max_retries = 3
        backoff = 1.0

        for attempt in range(max_retries):
            try:
                with httpx.Client(timeout=30.0) as client:
                    resp = client.post(url, headers=headers, json=payload)

                    # If model rejects thinkingConfig (HTTP 400), retry without it
                    if resp.status_code == 400 and "thinkingConfig" in payload.get("generationConfig", {}):
                        logger.info("thinkingConfig not supported by model; retrying without thinkingConfig.")
                        payload["generationConfig"].pop("thinkingConfig", None)
                        resp = client.post(url, headers=headers, json=payload)

                    if resp.status_code == 429:
                        logger.warning(f"Gemini API rate limited (attempt {attempt + 1}/{max_retries}).")
                        if attempt < max_retries - 1:
                            time.sleep(backoff)
                            backoff *= 2
                            continue
                        raise Exception("Gemini rate limit exceeded.")

                    resp.raise_for_status()
                    data = resp.json()

                    # Extract generated text from candidates
                    candidates = data.get("candidates", [])
                    if not candidates:
                        raise ValueError("No candidates returned by Gemini API")

                    parts = candidates[0].get("content", {}).get("parts", [])
                    if not parts or "text" not in parts[0]:
                        raise ValueError("No text part returned by Gemini API")

                    raw_text = parts[0]["text"]
                    parsed = json.loads(raw_text)

                    items = parsed.get("items") or parsed.get("posts") or []
                    results: List[AIAnalysisItem] = []

                    for item in items:
                        p_match = next((p for p in posts if p["id"] == item.get("post_id")), None)
                        if not p_match:
                            logger.warning("Ignoring Gemini analysis for an unknown post_id.")
                            continue
                        try:
                            validated = AIAnalysisItem(**item)
                            # VADER/local rules own sentiment classification. Gemini is used only
                            # for semantic extraction, summaries, and recommendations.
                            validated.sentiment = p_match.get("local_sentiment", "Neutral")
                            results.append(validated)
                        except ValidationError as ve:
                            logger.warning(f"Validation error for item in Gemini batch: {ve}")
                            results.append(heuristic_fallback_analyze(
                                post_id=p_match["id"],
                                content=p_match["content"],
                                title=p_match.get("title"),
                                local_sentiment=p_match.get("local_sentiment", "Neutral")
                            ))

                    # Ensure all posts in the batch are accounted for
                    returned_ids = {r.post_id for r in results}
                    for p in posts:
                        if p["id"] not in returned_ids:
                            results.append(heuristic_fallback_analyze(
                                post_id=p["id"],
                                content=p["content"],
                                title=p.get("title"),
                                local_sentiment=p.get("local_sentiment", "Neutral")
                            ))

                    return results

            except Exception as e:
                logger.error(f"Gemini API call failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(backoff)
                    backoff *= 2
                else:
                    logger.warning("Falling back to local heuristic analysis for this batch due to persistent Gemini error.")
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


gemini_service = GeminiService()
