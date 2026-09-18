import json
from unittest.mock import patch, MagicMock
import pytest
import httpx

from app.core.config import settings
from app.services.gemini_service import GeminiService, GeminiConfigurationError, GeminiProviderError, GeminiResponseError
from app.services.ai_service import AIService
from app.schemas.post_analysis import AIAnalysisItem


@pytest.fixture
def mock_gemini_success_response():
    """Mock standard successful Gemini generateContent JSON response."""
    payload = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": json.dumps({
                                "items": [
                                    {
                                        "post_id": 10,
                                        "sentiment": "Positive",
                                        "topic": "Running & Performance",
                                        "product": "Pegasus",
                                        "competitor": None,
                                        "summary": "Runner praises the Nike Pegasus for exceptional daily training support.",
                                        "key_positive": "Outstanding midsole cushioning and responsive rebound",
                                        "key_negative": None,
                                        "recommendation": "Feature user testimonials emphasizing durability in digital ads."
                                    },
                                    {
                                        "post_id": 11,
                                        "sentiment": "Mixed",
                                        "topic": "Pricing & Value",
                                        "product": "Air Jordan",
                                        "competitor": "Adidas",
                                        "summary": "Shoppers debate rising Jordan retail prices compared to Adidas models.",
                                        "key_positive": "Classic retro styling",
                                        "key_negative": "Steep price increase",
                                        "recommendation": "Introduce entry-level lifestyle colorways to capture price-sensitive buyers."
                                    }
                                ]
                            })
                        }
                    ]
                }
            }
        ]
    }
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = payload
    mock_resp.raise_for_status.return_value = None
    return mock_resp


def test_gemini_analyze_batch_success(mock_gemini_success_response):
    svc = GeminiService(api_key="mock-gemini-key", model="gemini-3.8-flash")

    posts = [
        {"id": 10, "content": "Pegasus 41 is the best running shoe of the year!", "title": "Pegasus review", "local_sentiment": "Positive"},
        {"id": 11, "content": "Jordans look great but Adidas is much cheaper nowadays.", "title": "Nike vs Adidas", "local_sentiment": "Mixed"},
    ]

    with patch("httpx.Client.post", return_value=mock_gemini_success_response) as mock_post:
        results = svc.analyze_batch(posts)

        assert mock_post.called
        assert len(results) == 2
        assert results[0].post_id == 10
        assert results[0].sentiment == "Positive"
        assert results[0].product == "Pegasus"
        assert results[0].topic == "Running & Performance"
        assert results[1].post_id == 11
        assert results[1].competitor == "Adidas"
        assert results[1].sentiment == "Mixed"


def test_gemini_owns_the_final_sentiment_classification(mock_gemini_success_response):
    svc = GeminiService(api_key="mock-gemini-key", model="gemini-3.8-flash")
    posts = [
        {
            "id": 10,
            "content": "This launch was awful and the app failed again.",
            "title": "Broken launch",
            "local_sentiment": "Negative",
        },
        {
            "id": 11,
            "content": "The design is fine.",
            "title": "Neutral design",
            "local_sentiment": "Neutral",
        },
    ]

    with patch("httpx.Client.post", return_value=mock_gemini_success_response):
        results = svc.analyze_batch(posts)

    assert [item.sentiment for item in results] == ["Positive", "Mixed"]


def test_gemini_missing_key_fails_without_fabricating_analysis():
    svc = GeminiService(api_key="", model="gemini-3.8-flash")
    posts = [
        {"id": 55, "content": "Nike Air Max is stylish but painful on long walks.", "title": "Air Max comfort", "local_sentiment": "Mixed"}
    ]

    with patch("httpx.Client.post") as mock_post:
        with pytest.raises(GeminiConfigurationError):
            svc.analyze_batch(posts)
        mock_post.assert_not_called()


def test_gemini_disabled_mode_fails_without_fabricating_analysis():
    svc = GeminiService(api_key="mock-key", model="gemini-3.8-flash")
    prev_state = settings.AI_ANALYSIS_ENABLED
    try:
        settings.AI_ANALYSIS_ENABLED = False
        posts = [{"id": 77, "content": "Nike shoes are good.", "title": "Shoes", "local_sentiment": "Positive"}]
        with patch("httpx.Client.post") as mock_post:
            with pytest.raises(GeminiConfigurationError):
                svc.analyze_batch(posts)
            mock_post.assert_not_called()
    finally:
        settings.AI_ANALYSIS_ENABLED = prev_state


def test_gemini_api_error_is_reported_without_fallback():
    svc = GeminiService(api_key="mock-key", model="gemini-3.8-flash")
    posts = [{"id": 88, "content": "Love my Nike Pegasus runners.", "title": "Pegasus", "local_sentiment": "Positive"}]

    mock_err_resp = MagicMock(spec=httpx.Response)
    mock_err_resp.status_code = 500
    mock_err_resp.raise_for_status.side_effect = httpx.HTTPStatusError("500 Server Error", request=MagicMock(), response=mock_err_resp)

    with patch("httpx.Client.post", return_value=mock_err_resp):
        with patch("time.sleep"):  # skip actual sleep
            with pytest.raises(GeminiProviderError):
                svc.analyze_batch(posts)


def test_gemini_partial_or_malformed_response_is_rejected_without_fallback():
    svc = GeminiService(api_key="mock-key", model="gemini-3.8-flash")
    posts = [
        {"id": 1, "content": "Nike Pegasus is great.", "title": "Review 1", "local_sentiment": "Positive"},
        {"id": 2, "content": "Puma is cheaper than Nike.", "title": "Review 2", "local_sentiment": "Neutral"}
    ]

    malformed_payload = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": json.dumps({
                                "items": [
                                    {
                                        "post_id": 1,
                                        "sentiment": "Positive",
                                        "topic": "Running",
                                        "product": "Pegasus",
                                        "summary": "Great shoe",
                                        "recommendation": "Keep it up"
                                    },
                                    {
                                        "post_id": 2,
                                        "sentiment": "Invalid_sentiment_non_pydantic",
                                        # Missing required summary & recommendation
                                    }
                                ]
                            })
                        }
                    ]
                }
            }
        ]
    }
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = malformed_payload
    mock_resp.raise_for_status.return_value = None

    with patch("httpx.Client.post", return_value=mock_resp):
        with pytest.raises(GeminiResponseError):
            svc.analyze_batch(posts)


def test_ai_service_provider_routing_gemini():
    svc = AIService()
    prev_gemini_key = settings.GEMINI_API_KEY
    try:
        settings.GEMINI_API_KEY = "test-gemini-key"
        assert svc.provider == "gemini"
        assert svc.active_model_name == settings.GEMINI_MODEL
    finally:
        settings.GEMINI_API_KEY = prev_gemini_key


def test_ai_service_never_routes_gemini_failure_to_another_provider():
    svc = AIService()
    prev_gemini_key = settings.GEMINI_API_KEY
    try:
        settings.GEMINI_API_KEY = "test-gemini-key"
        posts = [{"id": 12, "content": "Nike Pegasus", "title": "Nike", "local_sentiment": "Positive"}]
        with patch("app.services.ai_service.gemini_service.analyze_batch", side_effect=GeminiProviderError("Gemini network error")):
            with pytest.raises(GeminiProviderError):
                svc.analyze_batch(posts)
    finally:
        settings.GEMINI_API_KEY = prev_gemini_key
