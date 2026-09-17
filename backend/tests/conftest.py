import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models.base import Base
from app.database.session import get_db
from app.main import app
from app.models.organization import Organization
from app.models.brand import Brand
from app.models.competitor import Competitor
from app.models.tracked_keyword import TrackedKeyword
from app.core.config import settings
from app.services.gemini_service import gemini_service


@pytest.fixture(autouse=True)
def prevent_real_ai_calls(monkeypatch):
    """Automated tests must never inherit real provider credentials."""
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "")
    monkeypatch.setattr(gemini_service, "api_key", "")

@pytest.fixture
def db_session():
    # A fresh in-memory database per test is deliberate: collection error paths
    # call rollback(), and SQLite cannot reliably preserve an enclosing test
    # transaction after that. Per-test schemas guarantee isolation even when
    # application code commits or rolls back internally.
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = session_factory()

    org = Organization(name="Test Org")
    session.add(org)
    session.flush()
    brand = Brand(organization_id=org.id, name="Nike", description="Test brand description")
    session.add(brand)
    session.flush()
    session.add_all([
        Competitor(brand_id=brand.id, name="Adidas"),
        Competitor(brand_id=brand.id, name="Puma"),
        TrackedKeyword(brand_id=brand.id, keyword="Nike", category="brand"),
        TrackedKeyword(brand_id=brand.id, keyword="Pegasus", category="product"),
    ])
    session.commit()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
