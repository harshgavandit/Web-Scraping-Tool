import json
import time
from typing import List, Dict, Any, Optional
import httpx
from pydantic import ValidationError

from app.core.config import settings
from app.core.logging import logger
from app.schemas.post_analysis import AIAnalysisItem


class GeminiError(RuntimeError):
    """Base error for Gemini-only analysis failures."""


class GeminiConfigurationError(GeminiError):
    """Raised when Gemini analysis is not configured for use."""


class GeminiProviderError(GeminiError):
    """Raised when Gemini cannot complete a request after bounded retries."""


class GeminiResponseError(GeminiError):
    """Raised when Gemini returns incomplete or invalid structured output."""


class GeminiService:
    """
    Service client for the configured Google Gemini Flash model.
    Communicates via Google's Gemini REST API with structured JSON output and low-latency batching.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key if api_key is not None else settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL or "gemini-3.5-flash"
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    def analyze_batch(
        self,
        posts: List[Dict[str, Any]],
        strong_reasoning: bool = False
    ) -> List[AIAnalysisItem]:
        """
        Analyze a batch of posts using Gemini 3.8 Flash with structured JSON output.
        Uses Gemini exclusively. Configuration, provider, and response errors are
        surfaced to the caller and never replaced with synthetic analysis.
        """
        if not posts:
            return []

        if not self.api_key:
            raise GeminiConfigurationError("GEMINI_API_KEY is required for AI analysis.")
        if not settings.AI_ANALYSIS_ENABLED:
            raise GeminiConfigurationError("Gemini analysis is disabled by configuration.")

        post_summaries = []
        for p in posts:
            post_summaries.append({
                "id": p["id"],
                "title": p.get("title", ""),
                "content": p.get("content", "")[:2000],
                "source_url": p.get("source_url"),
                "local_sentiment": p.get("local_sentiment", "Neutral")
            })

        system_instruction = (
            "You are an expert brand listening and social intelligence analyst for brand marketing teams. "
            "Analyze the given batch of social posts about Nike and competitor brands. "
            "For each post, return strict JSON matching the schema with fields: "
            "post_id (int), sentiment (classify the article as exactly one of Positive, Negative, Neutral, or Mixed), "
            "topic (short string e.g. 'Running & Performance', 'Product Comfort & Fit', 'Pricing & Value', 'Build Quality & Durability', 'Customer Experience & Delivery', 'Style & Design', 'Sustainability & Ethics'), "
            "product (specific product e.g. 'Pegasus', 'Air Max', 'Air Jordan', 'Nike Running', or null), "
            "competitor (specific competitor e.g. 'Adidas', 'Puma', 'New Balance', 'Under Armour', or null), "
            "summary (1-2 concise sentences grounded only in this exact article; name its specific subject, product, claim, event, praise, or complaint so every summary is distinguishable from every other article), "
            "key_positive (short phrase or null), "
            "key_negative (short phrase or null), "
            "recommendation (1-2 practical, actionable marketing/business recommendations for Nike). "
            "Do not invent facts not in the post. Never return generic phrases such as 'general brand chatter', 'brand discussion', or wording that could apply unchanged to another article."
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
                        raise GeminiResponseError("No candidates returned by Gemini API")

                    parts = candidates[0].get("content", {}).get("parts", [])
                    if not parts or "text" not in parts[0]:
                        raise GeminiResponseError("No text part returned by Gemini API")

                    raw_text = parts[0]["text"]
                    try:
                        parsed = json.loads(raw_text)
                    except (TypeError, json.JSONDecodeError) as exc:
                        raise GeminiResponseError("Gemini returned invalid JSON.") from exc

                    items = parsed.get("items") or parsed.get("posts") or []
                    results: List[AIAnalysisItem] = []

                    for item in items:
                        p_match = next((p for p in posts if p["id"] == item.get("post_id")), None)
                        if not p_match:
                            logger.warning("Ignoring Gemini analysis for an unknown post_id.")
                            continue
                        try:
                            validated = AIAnalysisItem(**item)
                        except ValidationError as exc:
                            raise GeminiResponseError(f"Gemini returned an invalid analysis item: {exc}") from exc
                        validated.analysis_provider = "gemini"
                        validated.analysis_status = "completed"
                        results.append(validated)

                    # A partial response is not silently completed with fabricated data.
                    returned_ids = {r.post_id for r in results}
                    missing_ids = {p["id"] for p in posts} - returned_ids
                    if missing_ids:
                        raise GeminiResponseError(f"Gemini omitted post IDs: {sorted(missing_ids)}")

                    return results

            except GeminiResponseError:
                raise
            except Exception as e:
                logger.error(f"Gemini API call failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(backoff)
                    backoff *= 2
                else:
                    raise GeminiProviderError(f"Gemini analysis failed after {max_retries} attempts: {e}") from e

        return []


gemini_service = GeminiService()
