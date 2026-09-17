from typing import List, Dict, Any
from app.core.config import settings
from app.core.logging import logger
from app.schemas.post_analysis import AIAnalysisItem
from app.services.gemini_service import gemini_service
from app.services.openai_service import openai_service, heuristic_fallback_analyze


class AIService:
    """
    Unified AI Service orchestrator.
    Routes to Gemini 3.8 Flash as the primary AI model, with OpenAI as an optional secondary fallback,
    and local heuristic analysis as the zero-cost offline engine.
    """

    @property
    def provider(self) -> str:
        return (settings.AI_PROVIDER or "gemini").lower()

    @property
    def active_model_name(self) -> str:
        if not settings.AI_ANALYSIS_ENABLED:
            return "vader_heuristic"

        if self.provider == "gemini":
            if settings.GEMINI_API_KEY:
                return settings.GEMINI_MODEL or "gemini-3.8-flash"
            elif settings.OPENAI_API_KEY:
                return f"{settings.OPENAI_MODEL}_fallback"
            return "vader_heuristic"
        elif self.provider == "openai":
            if settings.OPENAI_API_KEY:
                return settings.OPENAI_MODEL or "gpt-4o-mini"
            return "vader_heuristic"

        return "vader_heuristic"

    def analyze_batch(
        self,
        posts: List[Dict[str, Any]],
        strong_reasoning: bool = False
    ) -> List[AIAnalysisItem]:
        """
        Processes a batch of posts using the primary provider (Gemini 3.8 Flash),
        falling back to OpenAI (if configured) or local heuristic analysis.
        """
        if not posts:
            return []

        if not settings.AI_ANALYSIS_ENABLED:
            return [
                heuristic_fallback_analyze(
                    post_id=p["id"],
                    content=p["content"],
                    title=p.get("title"),
                    local_sentiment=p.get("local_sentiment", "Neutral")
                )
                for p in posts
            ]

        # Primary: Gemini
        if self.provider == "gemini":
            if settings.GEMINI_API_KEY:
                try:
                    return gemini_service.analyze_batch(posts, strong_reasoning=strong_reasoning)
                except Exception as e:
                    logger.warning(f"Gemini service failed, checking for secondary fallback: {e}")
                    if settings.OPENAI_API_KEY:
                        logger.info("Attempting fallback to OpenAI service.")
                        return openai_service.analyze_batch(posts)
                    return [
                        heuristic_fallback_analyze(
                            post_id=p["id"],
                            content=p["content"],
                            title=p.get("title"),
                            local_sentiment=p.get("local_sentiment", "Neutral")
                        )
                        for p in posts
                    ]
            elif settings.OPENAI_API_KEY:
                logger.info("Gemini API key not set; falling back to configured OpenAI API key.")
                return openai_service.analyze_batch(posts)
            else:
                return gemini_service.analyze_batch(posts, strong_reasoning=strong_reasoning)

        # Alternative: OpenAI
        elif self.provider == "openai":
            if settings.OPENAI_API_KEY:
                return openai_service.analyze_batch(posts)
            elif settings.GEMINI_API_KEY:
                logger.info("OpenAI API key not set; falling back to configured Gemini API key.")
                return gemini_service.analyze_batch(posts, strong_reasoning=strong_reasoning)
            else:
                return openai_service.analyze_batch(posts)

        # Default fallback
        return [
            heuristic_fallback_analyze(
                post_id=p["id"],
                content=p["content"],
                title=p.get("title"),
                local_sentiment=p.get("local_sentiment", "Neutral")
            )
            for p in posts
        ]


ai_service = AIService()
