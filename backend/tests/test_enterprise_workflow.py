from app.models.product_intelligence import IssueCluster, Product
from app.services.alert_service import dispatch_email_alerts, sync_reputation_alerts
from app.utils.datetime_utils import utc_now


def test_risk_alert_can_be_acknowledged_end_to_end(client, db_session):
    product = Product(brand_id=1, name="Pegasus", aliases=[])
    db_session.add(product)
    db_session.flush()
    cluster = IssueCluster(
        brand_id=1,
        product_id=product.id,
        title="Pegasus durability concerns",
        aspect="Durability",
        mention_count=8,
        unique_sources=4,
        growth_pct=75,
        attention_score=70,
        risk_score=72,
        risk_level="Elevated",
        confidence=0.88,
        first_seen_at=utc_now(),
        last_seen_at=utc_now(),
    )
    db_session.add(cluster)
    db_session.flush()
    sync_reputation_alerts(db_session, brand_id=1)
    db_session.commit()

    listing = client.get("/api/alerts?brand_id=1")
    assert listing.status_code == 200
    alert = listing.json()[0]
    assert alert["severity"] == "Elevated"
    assert alert["status"] == "open"
    assert alert["evidence_count"] == 8

    acknowledgement = client.patch(f"/api/alerts/{alert['id']}", json={"status": "acknowledged"})
    assert acknowledgement.status_code == 200
    assert acknowledgement.json()["status"] == "acknowledged"
    assert acknowledgement.json()["acknowledged_at"] is not None


def test_intelligence_export_is_a_downloadable_csv(client, db_session):
    product = Product(brand_id=1, name="Pegasus", aliases=[])
    db_session.add(product)
    db_session.flush()
    db_session.add(IssueCluster(
        brand_id=1,
        product_id=product.id,
        title="Pegasus price concerns",
        aspect="Price & Value",
        mention_count=5,
        unique_sources=3,
        growth_pct=20,
        attention_score=60,
        risk_score=55,
        risk_level="Elevated",
        confidence=0.8,
        first_seen_at=utc_now(),
        last_seen_at=utc_now(),
    ))
    db_session.commit()

    response = client.get("/api/intelligence/export.csv?brand_id=1")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment; filename=" in response.headers["content-disposition"]
    assert "Pegasus price concerns" in response.text
    assert "independent_sources" in response.text


def test_intelligence_export_is_a_downloadable_pdf(client, db_session):
    product = Product(brand_id=1, name="Pegasus", aliases=[])
    db_session.add(product)
    db_session.flush()
    db_session.add(IssueCluster(
        brand_id=1, product_id=product.id, title="Pegasus durability concerns",
        aspect="Durability", mention_count=7, unique_sources=4, growth_pct=50,
        attention_score=71, risk_score=68, risk_level="Elevated", confidence=0.9,
        first_seen_at=utc_now(), last_seen_at=utc_now(),
    ))
    db_session.commit()

    response = client.get("/api/intelligence/export.pdf?brand_id=1")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment; filename=" in response.headers["content-disposition"]
    assert response.content.startswith(b"%PDF-")


def test_high_risk_alert_email_is_sent_once_and_audited(db_session, monkeypatch):
    from app.core.config import settings

    product = Product(brand_id=1, name="Pegasus", aliases=[])
    db_session.add(product)
    db_session.flush()
    db_session.add(IssueCluster(
        brand_id=1, product_id=product.id, title="Pegasus outsole failures",
        aspect="Durability", mention_count=9, unique_sources=5, growth_pct=90,
        attention_score=80, risk_score=79, risk_level="Critical", confidence=0.94,
        first_seen_at=utc_now(), last_seen_at=utc_now(),
    ))
    db_session.flush()
    alerts = sync_reputation_alerts(db_session, brand_id=1)
    monkeypatch.setattr(settings, "EMAIL_ALERTS_ENABLED", True)
    monkeypatch.setattr(settings, "EMAIL_ALERT_RECIPIENTS", "brand@example.com,pr@example.com")
    sent = []

    class Sender:
        def send(self, recipients, subject, text_body, html_body):
            sent.append((recipients, subject, text_body, html_body))

    dispatch_email_alerts(db_session, alerts, sender=Sender())
    dispatch_email_alerts(db_session, alerts, sender=Sender())
    db_session.commit()

    assert len(sent) == 1
    assert sent[0][0] == ["brand@example.com", "pr@example.com"]
    assert "Critical" in sent[0][1]
    assert alerts[0].email_status == "sent"
    assert alerts[0].email_sent_at is not None
    assert alerts[0].email_recipients == ["brand@example.com", "pr@example.com"]


def test_source_and_ai_audit_endpoint_returns_traceability(client, db_session):
    from app.models.post import Post
    from app.models.post_analysis import PostAnalysis
    from app.models.search_discovery import SearchQuery, SearchRun

    query = SearchQuery(brand_id=1, provider="google_search", query='"Nike" reviews', category="customer_feedback")
    db_session.add(query)
    db_session.flush()
    db_session.add(SearchRun(query_id=query.id, provider="google_search", status="completed", results_found=4, results_new=2, completed_at=utc_now()))
    post = Post(brand_id=1, source="google_search", external_id="audit-1", url="https://example.org/nike", content="Nike review", content_hash="audit-hash", published_at=utc_now())
    db_session.add(post)
    db_session.flush()
    db_session.add(PostAnalysis(post_id=post.id, sentiment="Neutral", topic="Review", model_used="gemini-3.8-flash", analysis_provider="gemini", analysis_status="completed"))
    db_session.commit()

    response = client.get("/api/audit?brand_id=1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_runs"][0]["provider"] == "google_search"
    assert payload["ai_analyses"][0]["provider"] == "gemini"
    assert payload["ai_analyses"][0]["source_url"] == "https://example.org/nike"


def test_saved_views_crud_lifecycle(client, db_session):
    create_res = client.post("/api/saved-views", json={
        "brand_id": 1,
        "name": "Nike Running - Complaints",
        "description": "Weekly negative feedback across running lines",
        "team": "category",
        "filters": {"sentiment": "Negative", "search": "Pegasus"},
        "is_default": True,
    })
    assert create_res.status_code == 201
    view_id = create_res.json()["id"]
    assert create_res.json()["name"] == "Nike Running - Complaints"
    assert create_res.json()["is_default"] is True

    list_res = client.get("/api/saved-views?brand_id=1")
    assert list_res.status_code == 200
    assert any(v["id"] == view_id for v in list_res.json())

    update_res = client.patch(f"/api/saved-views/{view_id}", json={
        "name": "Nike Running - Critical Issues",
    })
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "Nike Running - Critical Issues"

    del_res = client.delete(f"/api/saved-views/{view_id}")
    assert del_res.status_code == 204
    assert client.get(f"/api/saved-views/{view_id}").status_code == 404


def test_executive_summary_includes_ownership_priority_and_evidence(client, db_session):
    from app.models.post import Post
    from app.models.post_analysis import PostAnalysis
    from app.models.product_intelligence import MentionEvidence

    post = Post(
        brand_id=1,
        source="google_search",
        external_id="summary-evidence-1",
        title="Nike delivery delays",
        content="The customer service was terrible and shipping delayed for weeks.",
        content_hash="summary-evidence-hash-1",
        published_at=utc_now(),
    )
    db_session.add(post)
    db_session.flush()
    db_session.add(PostAnalysis(
        post_id=post.id,
        sentiment="Negative",
        sentiment_score=-0.8,
        topic="Customer Experience & Delivery",
    ))
    db_session.add(MentionEvidence(
        post_id=post.id,
        aspect="Customer Experience",
        sentiment="Negative",
        sentiment_score=-0.8,
        evidence_quote="Customer service was terrible and shipping delayed for weeks.",
        confidence=0.9,
    ))
    db_session.commit()

    res = client.get("/api/dashboard/summary?brand_id=1&days=30&refresh=true")
    assert res.status_code == 200
    exec_summary = res.json()["executive_summary"]
    assert exec_summary["recommendation_owner"] == "Customer Experience & Fulfillment"
    assert exec_summary["recommendation_priority"] in ("P0", "P1", "P2")
    assert len(exec_summary["evidence_quotes"]) >= 1
