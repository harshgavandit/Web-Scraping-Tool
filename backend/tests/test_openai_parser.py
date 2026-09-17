import pytest
from pydantic import ValidationError
from app.schemas.post_analysis import AIAnalysisItem
from app.services.openai_service import heuristic_fallback_analyze, OpenAIService
from app.core.config import settings


def test_ai_analysis_item_validation():
    valid_data = {
        "post_id": 42,
        "sentiment": "Mixed",
        "topic": "Running Shoes / Pricing",
        "product": "Pegasus",
        "competitor": "Adidas",
        "summary": "Users like comfort but find pricing high.",
        "key_positive": "Comfortable ReactX foam",
        "key_negative": "Steep price increase",
        "recommendation": "Strengthen value messaging in marketing campaigns."
    }
    item = AIAnalysisItem(**valid_data)
    assert item.post_id == 42
    assert item.sentiment == "Mixed"
    assert item.product == "Pegasus"


def test_heuristic_fallback_extraction():
    content = "Love my new Nike Pegasus. Extremely comfortable for long runs but they're getting expensive."
    item = heuristic_fallback_analyze(post_id=101, content=content, local_sentiment="Mixed")

    assert item.post_id == 101
    assert item.product == "Pegasus"
    assert "comfort" in (item.key_positive or "").lower() or "cushion" in (item.key_positive or "").lower()
    assert item.summary is not None
    assert item.recommendation is not None


def test_openai_service_batch_fallback():
    # When no API key is provided, analyze_batch returns valid items via heuristic
    svc = OpenAIService()
    svc.client = None

    posts = [
        {"id": 1, "content": "Nike Air Max is stylish but Adidas is cheaper.", "title": "Nike vs Adidas", "local_sentiment": "Mixed"},
        {"id": 2, "content": "SNKRS app crashed again during Jordan drop!", "title": "SNKRS drop", "local_sentiment": "Negative"}
    ]
    results = svc.analyze_batch(posts)
    assert len(results) == 2
    assert results[0].post_id == 1
    assert results[0].competitor == "Adidas"
    assert results[1].post_id == 2
    assert results[1].product == "Air Jordan"


def test_openai_disabled_mode():
    svc = OpenAIService()
    prev_state = settings.AI_ANALYSIS_ENABLED
    try:
        settings.AI_ANALYSIS_ENABLED = False
        posts = [{"id": 99, "content": "Nike running shoes are fast.", "title": "Run review", "local_sentiment": "Positive"}]
        results = svc.analyze_batch(posts)
        assert len(results) == 1
        assert results[0].post_id == 99
        assert results[0].sentiment == "Positive"
        assert results[0].summary is not None
        assert results[0].recommendation is not None
    finally:
        settings.AI_ANALYSIS_ENABLED = prev_state


def test_malformed_ai_item_validation_error():
    # If a payload is missing required fields, ValidationError is raised by Pydantic
    invalid_data = {
        "post_id": 1,
        # missing summary & recommendation & sentiment
    }
    with pytest.raises(ValidationError):
        AIAnalysisItem(**invalid_data)


def test_ai_analysis_item_rejects_unsupported_sentiment():
    with pytest.raises(ValidationError):
        AIAnalysisItem(
            post_id=1,
            sentiment="Very Positive",
            topic="Running",
            summary="A summary",
            recommendation="A recommendation",
        )
