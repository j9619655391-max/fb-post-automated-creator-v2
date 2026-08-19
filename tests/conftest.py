import os
import sys

import pytest
from fastapi.testclient import TestClient

# Configure the database before importing the application.
os.environ["DATABASE_URL"] = "sqlite:///file:testdb?mode=memory&cache=shared&uri=true"

# Ensure app package is on path.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.core.database import Base, engine, SessionLocal


@pytest.fixture(scope="function")
def client():
    """Test client with an isolated shared in-memory SQLite database."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
def db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def api():
    """API prefix from config (for example, /api/v1)."""
    from app.core.config import settings
    return settings.api_prefix


@pytest.fixture(scope="function")
def auth_headers(client, api):
    """Create a test user and return a valid JWT Authorization header."""
    signup = client.post(
        f"{api}/auth/signup",
        json={
            "username": "test-user",
            "email": "test-user@example.com",
            "full_name": "Test User",
            "password": "test-password-123",
        },
    )
    assert signup.status_code == 200, signup.text

    login = client.post(
        f"{api}/auth/login",
        data={"username": "test-user", "password": "test-password-123"},
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}
