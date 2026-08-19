from datetime import datetime, timezone
from urllib.parse import parse_qs, urlparse

from app.core.config import settings
from app.models.meta_oauth import OAuthState
from app.core.database import SessionLocal


def test_facebook_oauth_initiation_uses_expiring_server_state(client, api, auth_headers, monkeypatch):
    monkeypatch.setattr(settings, "facebook_app_id", "facebook-test-app")
    monkeypatch.setattr(settings, "facebook_redirect_uri", "http://localhost/callback")

    response = client.post(f"{api}/auth/facebook/login", headers=auth_headers)
    assert response.status_code == 200, response.text
    authorize_url = response.json()["authorize_url"]
    state = parse_qs(urlparse(authorize_url).query)["state"][0]

    db = SessionLocal()
    try:
        oauth_state = db.query(OAuthState).filter(OAuthState.state == state).one()
        assert oauth_state.provider == "facebook"
        assert oauth_state.consumed_at is None
        assert oauth_state.expires_at is not None
        assert oauth_state.expires_at.replace(tzinfo=timezone.utc) > datetime.now(timezone.utc)
    finally:
        db.close()

    legacy = client.get(f"{api}/auth/facebook/login?token=not-a-jwt")
    assert legacy.status_code == 404


def test_linkedin_oauth_initiation_uses_expiring_server_state(client, api, auth_headers, monkeypatch):
    monkeypatch.setattr(settings, "linkedin_client_id", "linkedin-test-client")
    monkeypatch.setattr(settings, "linkedin_redirect_uri", "http://localhost/linkedin-callback")

    response = client.post(f"{api}/auth/linkedin/login", headers=auth_headers)
    assert response.status_code == 200, response.text
    authorize_url = response.json()["authorize_url"]
    state = parse_qs(urlparse(authorize_url).query)["state"][0]

    db = SessionLocal()
    try:
        oauth_state = db.query(OAuthState).filter(OAuthState.state == state).one()
        assert oauth_state.provider == "linkedin"
        assert oauth_state.consumed_at is None
        assert oauth_state.expires_at is not None
    finally:
        db.close()

    legacy = client.get(f"{api}/auth/linkedin/login?token=not-a-jwt")
    assert legacy.status_code == 404
