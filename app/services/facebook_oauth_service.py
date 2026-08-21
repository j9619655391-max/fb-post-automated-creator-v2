"""Facebook OAuth service (single Meta App; user consent only)."""
import secrets
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.token_crypto import encrypt_token
from app.core.meta_api_errors import handle_meta_response
from app.models.meta_oauth import OAuthState, MetaUserToken
from app.models.meta_page import MetaPage
from app.services.audit_service import AuditService


# Scopes for Page listing/posting and Instagram professional-account publishing.
OAUTH_SCOPES = settings.facebook_oauth_scopes

META_OAUTH_AUTHORIZE = "https://www.facebook.com/v18.0/dialog/oauth"
META_OAUTH_ACCESS_TOKEN = "https://graph.facebook.com/v18.0/oauth/access_token"
META_LONG_LIVED_TOKEN = "https://graph.facebook.com/v18.0/oauth/access_token"


def get_authorize_url(db: Session, user_id: int) -> str:
    """
    Create OAuth state and return Facebook authorize URL.
    Raises ValueError if Facebook app not configured.
    """
    app_id = settings.facebook_app_id
    redirect_uri = settings.facebook_redirect_uri
    if not app_id or not redirect_uri:
        raise ValueError("Facebook OAuth not configured (FACEBOOK_APP_ID, FACEBOOK_REDIRECT_URI)")
    state = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    db.add(
        OAuthState(
            state=state,
            provider="facebook",
            user_id=user_id,
            expires_at=now + timedelta(minutes=10),
        )
    )
    db.commit()
    params = {
        "client_id": app_id,
        "redirect_uri": redirect_uri,
        "state": state,
        "scope": OAUTH_SCOPES,
        "response_type": "code",
    }
    return f"{META_OAUTH_AUTHORIZE}?{urlencode(params)}"


def exchange_code(db: Session, code: str, state: str) -> int:
    """
    Validate state, exchange code for access token, store encrypted token.
    Returns user_id. Deletes OAuth state after use.
    Raises ValueError on invalid state/code or missing config.
    """
    app_id = settings.facebook_app_id
    app_secret = settings.facebook_app_secret
    redirect_uri = settings.facebook_redirect_uri
    if not app_id or not app_secret or not redirect_uri:
        raise ValueError("Facebook OAuth not configured")
    oauth_state = db.query(OAuthState).filter(
        OAuthState.state == state,
        OAuthState.provider == "facebook",
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

    params = {
        "client_id": app_id,
        "client_secret": app_secret,
        "redirect_uri": redirect_uri,
        "code": code,
    }
    try:
        with httpx.Client() as client:
            resp = client.get(META_OAUTH_ACCESS_TOKEN, params=params)
            if not resp.is_success:
                handle_meta_response(resp, "Facebook login")
            data = resp.json()
    except ValueError:
        raise
    except httpx.RequestError as e:
        raise ValueError("Facebook login: Request failed. Please try again.") from e
    access_token = data.get("access_token")
    if not access_token:
        raise ValueError("No access_token in Meta response")
    expires_in = data.get("expires_in")
    # Exchange for long-lived token (≈60 days) when we have app credentials
    if app_id and app_secret:
        try:
            with httpx.Client() as client:
                long_resp = client.get(
                    META_LONG_LIVED_TOKEN,
                    params={
                        "grant_type": "fb_exchange_token",
                        "client_id": app_id,
                        "client_secret": app_secret,
                        "fb_exchange_token": access_token,
                    },
                )
                if long_resp.is_success:
                    long_data = long_resp.json()
                    if long_data.get("access_token"):
                        access_token = long_data["access_token"]
                        expires_in = long_data.get("expires_in")
        except Exception:
            pass  # Keep short-lived token if exchange fails
    encrypted = encrypt_token(access_token)
    expires_at = (datetime.now(timezone.utc) + timedelta(seconds=expires_in)) if expires_in else None
    existing = db.query(MetaUserToken).filter(MetaUserToken.user_id == user_id).first()
    if existing:
        existing.access_token_encrypted = encrypted
        existing.meta_user_id = data.get("user_id")
        existing.expires_at = expires_at
    else:
        db.add(MetaUserToken(
            user_id=user_id,
            access_token_encrypted=encrypted,
            meta_user_id=data.get("user_id"),
            expires_at=expires_at,
        ))
    AuditService.log_action(
        db,
        action="facebook.connected",
        entity_type="meta_oauth",
        entity_id=None,
        user_id=user_id,
        description="User connected Facebook account",
        metadata={"long_lived": bool(app_id and app_secret)},
    )
    db.commit()
    return user_id


def disconnect_facebook(db: Session, user_id: int) -> bool:
    """
    Remove user's Facebook connection: delete MetaUserToken and MetaPages.
    User must re-run OAuth and sync pages to use Facebook again. Returns True if disconnected.
    """
    had_token = db.query(MetaUserToken).filter(MetaUserToken.user_id == user_id).first() is not None
    db.query(MetaPage).filter(MetaPage.user_id == user_id).delete()
    db.query(MetaUserToken).filter(MetaUserToken.user_id == user_id).delete()
    if had_token:
        AuditService.log_action(
            db,
            action="facebook.disconnected",
            entity_type="meta_oauth",
            entity_id=None,
            user_id=user_id,
            description="User disconnected Facebook account",
            metadata={},
        )
    db.commit()
    return had_token
def refresh_long_lived_token(db: Session, user_token: MetaUserToken) -> bool:
    """
    Refresh a long-lived Meta token.
    Long-lived tokens can be refreshed once per day if they are still valid.
    Returns True if refreshed, False otherwise.
    """
    from app.core.token_crypto import decrypt_token
    
    app_id = settings.facebook_app_id
    app_secret = settings.facebook_app_secret
    if not app_id or not app_secret:
        return False
        
    current_token = decrypt_token(user_token.access_token_encrypted)
    
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "fb_exchange_token": current_token,
    }
    
    try:
        with httpx.Client() as client:
            resp = client.get(META_LONG_LIVED_TOKEN, params=params)
            if resp.is_success:
                data = resp.json()
                new_token = data.get("access_token")
                expires_in = data.get("expires_in")
                
                if new_token:
                    user_token.access_token_encrypted = encrypt_token(new_token)
                    if expires_in:
                        user_token.expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
                    db.commit()
                    
                    AuditService.log_action(
                        db, "token.refreshed", "user", user_token.user_id, user_token.user_id,
                        f"Meta access token for user {user_token.user_id} was automatically refreshed."
                    )
                    return True
    except Exception as e:
        # Log failure but don't crash the task
        AuditService.log_action(
            db, "token.refresh_failed", "user", user_token.user_id, user_token.user_id,
            f"Failed to auto-refresh Meta token: {str(e)}"
        )
        
    return False
