from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.token_crypto import decrypt_token
from app.models.linkedin_account import LinkedInAccount
from app.models.linkedin_oauth import LinkedInUserToken
from app.models.meta_oauth import MetaUserToken
from app.models.meta_page import MetaPage


def _configured(*values: str | None) -> bool:
    return all(value and value.strip() for value in values)


def _safe_http_error(response: httpx.Response) -> str:
    if response.status_code in {401, 403}:
        return "provider rejected the stored token or required permissions"
    if response.status_code == 429:
        return "provider rate limit reached"
    if response.status_code >= 500:
        return "provider temporarily unavailable"
    return f"provider validation returned HTTP {response.status_code}"


def _meta_readiness(db: Session, user_id: int) -> dict[str, Any]:
    configured = _configured(
        settings.facebook_app_id,
        settings.facebook_app_secret,
        settings.facebook_redirect_uri,
        settings.token_encryption_key,
    )
    token = db.query(MetaUserToken).filter(MetaUserToken.user_id == user_id).first()
    pages = db.query(MetaPage).filter(MetaPage.user_id == user_id).all()
    result: dict[str, Any] = {
        "configured": configured,
        "connected": token is not None,
        "remote_check": "not_run",
        "pages_count": len(pages),
        "publish_ready": False,
        "reason": None,
    }
    if not configured:
        result["reason"] = "Meta OAuth app, callback, and token encryption settings are required"
        return result
    if not token:
        result["reason"] = "connect a Meta account before sandbox validation"
        return result
    try:
        access_token = decrypt_token(token.access_token_encrypted)
        with httpx.Client(timeout=10.0) as client:
            response = client.get(
                "https://graph.facebook.com/v18.0/me/accounts",
                params={"fields": "id,name,instagram_business_account", "limit": 1},
                headers={"Authorization": f"Bearer {access_token}"},
            )
        if response.is_success:
            result["remote_check"] = "passed"
            result["publish_ready"] = bool(pages)
            if not pages:
                result["reason"] = "Meta token is valid but no synced Page is available"
        else:
            result["remote_check"] = "failed"
            result["reason"] = _safe_http_error(response)
    except (httpx.RequestError, ValueError, TypeError):
        result["remote_check"] = "failed"
        result["reason"] = "stored Meta token could not be validated"
    return result


def _instagram_readiness(meta: dict[str, Any], linked_count: int) -> dict[str, Any]:
    ready = meta["remote_check"] == "passed" and linked_count > 0
    return {
        "configured": meta["configured"],
        "connected": linked_count > 0,
        "remote_check": meta["remote_check"],
        "publish_ready": ready,
        "linked_accounts_count": linked_count,
        "reason": None if ready else "connect a professional Instagram account to a synced Facebook Page and pass the Meta read-only check",
        "meta_dependency": "Instagram publishing requires a connected professional account and Meta authorization",
    }


def _linkedin_readiness(db: Session, user_id: int) -> dict[str, Any]:
    configured = _configured(
        settings.linkedin_client_id,
        settings.linkedin_client_secret,
        settings.linkedin_redirect_uri,
        settings.token_encryption_key,
    )
    token = db.query(LinkedInUserToken).filter(LinkedInUserToken.user_id == user_id).first()
    accounts = db.query(LinkedInAccount).filter(LinkedInAccount.user_id == user_id).all()
    organization_accounts = [account for account in accounts if account.account_type == "organization"]
    result: dict[str, Any] = {
        "configured": configured,
        "connected": token is not None,
        "remote_check": "not_run",
        "accounts_count": len(accounts),
        "organization_accounts_count": len(organization_accounts),
        "publish_ready": False,
        "reason": None,
    }
    if not configured:
        result["reason"] = "LinkedIn OAuth app, callback, and token encryption settings are required"
        return result
    if not token:
        result["reason"] = "connect a LinkedIn account before sandbox validation"
        return result
    try:
        access_token = decrypt_token(token.access_token_encrypted)
        with httpx.Client(timeout=10.0) as client:
            response = client.get(
                "https://api.linkedin.com/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
        if response.is_success:
            result["remote_check"] = "passed"
            result["publish_ready"] = bool(organization_accounts)
            if not organization_accounts:
                result["reason"] = "member identity is valid but no organization account is synced"
        else:
            result["remote_check"] = "failed"
            result["reason"] = _safe_http_error(response)
    except (httpx.RequestError, ValueError, TypeError):
        result["remote_check"] = "failed"
        result["reason"] = "stored LinkedIn token could not be validated"
    return result


def collect_platform_sandbox_readiness(db: Session, user_id: int) -> dict[str, Any]:
    meta = _meta_readiness(db, user_id)
    linked_instagram_count = db.query(MetaPage).filter(
        MetaPage.user_id == user_id,
        MetaPage.instagram_business_account_id.isnot(None),
    ).count()
    return {
        "facebook": meta,
        "instagram": _instagram_readiness(meta, linked_instagram_count),
        "linkedin": _linkedin_readiness(db, user_id),
        "publishing_attempted": False,
    }
