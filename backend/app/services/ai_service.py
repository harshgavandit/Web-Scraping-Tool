from typing import Any, Dict, List

from app.core.config import settings
from app.schemas.post_analysis import AIAnalysisItem
from app.services.gemini_service import GeminiConfigurationError, gemini_service


class AIService:
    """Routes all semantic analysis exclusively to the configured Gemini model."""

    @property
    def provider(self) -> str:
        return "gemini"

    @property
    def active_model_name(self) -> str:
        return settings.GEMINI_MODEL or "gemini-3.5-flash"

    def analyze_batch(
        self,
        posts: List[Dict[str, Any]],
        strong_reasoning: bool = False,
    ) -> List[AIAnalysisItem]:
        if not posts:
            return []
        if not settings.GEMINI_API_KEY:
            raise GeminiConfigurationError("GEMINI_API_KEY is required for AI analysis.")
        return gemini_service.analyze_batch(posts, strong_reasoning=strong_reasoning)


ai_service = AIService()
