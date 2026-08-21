"""LinkedIn OAuth service (user consent only)."""
import secrets
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.token_crypto import encrypt_token, decrypt_token
from app.models.meta_oauth import OAuthState
from app.models.linkedin_oauth import LinkedInUserToken
from app.services.audit_service import AuditService


# Scopes for posting on behalf of the user
OAUTH_SCOPES = settings.linkedin_oauth_scopes

LINKEDIN_OAUTH_AUTHORIZE = "https://www.linkedin.com/oauth/v2/authorization"
LINKEDIN_OAUTH_ACCESS_TOKEN = "https://www.linkedin.com/oauth/v2/accessToken"


def get_authorize_url(db: Session, user_id: int) -> str:
    """
    Create OAuth state and return LinkedIn authorize URL.
    Raises ValueError if LinkedIn app not configured.
    """
    client_id = settings.linkedin_client_id
    redirect_uri = settings.linkedin_redirect_uri
    if not client_id or not redirect_uri:
        raise ValueError("LinkedIn OAuth not configured (LINKEDIN_CLIENT_ID, LINKEDIN_REDIRECT_URI)")
    
    state = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    db.add(
        OAuthState(
            state=state,
            provider="linkedin",
            user_id=user_id,
            expires_at=now + timedelta(minutes=10),
        )
    )
    db.commit()
    
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state,
        "scope": OAUTH_SCOPES,
    }
    return f"{LINKEDIN_OAUTH_AUTHORIZE}?{urlencode(params)}"


def exchange_code(db: Session, code: str, state: str) -> int:
    """
    Validate state, exchange code for access token, store encrypted token.
    Returns user_id. Deletes OAuth state after use.
    """
    client_id = settings.linkedin_client_id
    client_secret = settings.linkedin_client_secret
    redirect_uri = settings.linkedin_redirect_uri
    if not client_id or not client_secret or not redirect_uri:
        raise ValueError("LinkedIn OAuth not configured")
    
    oauth_state = db.query(OAuthState).filter(
        OAuthState.state == state,
        OAuthState.provider == "linkedin",
        OAuthState.consumed_at.is_(None),
    ).first()
    now = datetime.now(timezone.utc)
    if not oauth_state:
        raise ValueError("Invalid or expired OAuth state")
    expires_at = oauth_state.expires_at
    if not expires_at:
        db.delete(oauth_state)
        db.commit()
        raise ValueError("Invalid or expired OAuth state")
    if not expires_at.tzinfo:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= now:
        db.delete(oauth_state)
        db.commit()
        raise ValueError("Invalid or expired OAuth state")
    user_id = oauth_state.user_id
    oauth_state.consumed_at = now
    db.commit()

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
    }
    
    try:
        with httpx.Client() as client:
            resp = client.post(LINKEDIN_OAUTH_ACCESS_TOKEN, data=data)
            if not resp.is_success:
                raise ValueError(f"LinkedIn login failed: {resp.text}")
            resp_data = resp.json()
    except httpx.RequestError as e:
        raise ValueError("LinkedIn login: Request failed. Please try again.") from e

    access_token = resp_data.get("access_token")
    if not access_token:
        raise ValueError("No access_token in LinkedIn response")
    
    expires_in = resp_data.get("expires_in")
    encrypted = encrypt_token(access_token)
    expires_at = (datetime.now(timezone.utc) + timedelta(seconds=expires_in)) if expires_in else None
    
    # Get LinkedIn User ID (urn)
    try:
        with httpx.Client() as client:
            user_info_resp = client.get(
                "https://api.linkedin.com/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            if user_info_resp.is_success:
                user_info = user_info_resp.json()
                linkedin_user_id = user_info.get("sub") # In OpenID Connect, 'sub' is the unique ID
            else:
                linkedin_user_id = None
    except Exception:
        linkedin_user_id = None

    existing = db.query(LinkedInUserToken).filter(LinkedInUserToken.user_id == user_id).first()
    if existing:
        existing.access_token_encrypted = encrypted
        existing.linkedin_user_id = linkedin_user_id
        existing.expires_at = expires_at
    else:
        db.add(LinkedInUserToken(
            user_id=user_id,
            access_token_encrypted=encrypted,
            linkedin_user_id=linkedin_user_id,
            expires_at=expires_at,
        ))
    
    AuditService.log_action(
        db,
        action="linkedin.connected",
        entity_type="linkedin_oauth",
        entity_id=None,
        user_id=user_id,
        description="User connected LinkedIn account",
        metadata={},
    )
    db.commit()
    return user_id


def disconnect_linkedin(db: Session, user_id: int) -> bool:
    """Remove user's LinkedIn connection."""
    had_token = db.query(LinkedInUserToken).filter(LinkedInUserToken.user_id == user_id).first() is not None
    db.query(LinkedInUserToken).filter(LinkedInUserToken.user_id == user_id).delete()
    if had_token:
        AuditService.log_action(
            db,
            action="linkedin.disconnected",
            entity_type="linkedin_oauth",
            entity_id=None,
            user_id=user_id,
            description="User disconnected LinkedIn account",
            metadata={},
        )
    db.commit()
    return had_token
