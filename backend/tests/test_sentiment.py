from app.services.sentiment_service import analyze_local_sentiment


def test_positive_sentiment():
    text = "Absolutely love my new Nike Pegasus! The most comfortable running shoes I've ever owned."
    label, score, _ = analyze_local_sentiment(text)
    assert label == "Positive"
    assert score > 0.3


def test_negative_sentiment():
    text = "Terrible experience with Nike customer support. The shoe sole tore on day one and they refused my refund."
    label, score, _ = analyze_local_sentiment(text)
    assert label == "Negative"
    assert score < -0.3


def test_mixed_sentiment():
    text = "Nike Pegasus is extremely comfortable for long marathon runs, but the price is becoming way too expensive."
    label, score, needs_ai = analyze_local_sentiment(text)
    assert label == "Mixed"
    assert needs_ai is True


def test_neutral_sentiment():
    text = "Nike released the new colorways yesterday for the summer schedule."
    label, score, _ = analyze_local_sentiment(text)
    assert label == "Neutral"
    assert -0.2 < score < 0.2
