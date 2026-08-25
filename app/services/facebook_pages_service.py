"""Facebook Pages service: fetch pages from Graph API, store encrypted page tokens."""
from typing import List

import httpx
from sqlalchemy.orm import Session

from app.core.token_crypto import encrypt_token, decrypt_token
from app.core.meta_api_errors import handle_meta_response, TokenInvalidError
from app.models.meta_oauth import MetaUserToken
from app.models.meta_page import MetaPage
from app.services.audit_service import AuditService


META_GRAPH_BASE = "https://graph.facebook.com/v18.0"


def _get_user_token(db: Session, user_id: int) -> str:
    """Return decrypted user access token. Raises ValueError if not found or invalid."""
    row = db.query(MetaUserToken).filter(MetaUserToken.user_id == user_id).first()
    if not row:
        raise ValueError("User has not connected Facebook; complete OAuth first")
    return decrypt_token(row.access_token_encrypted)


def _clear_user_token(db: Session, user_id: int) -> None:
    """Remove stored Meta user token (e.g. after expiry/invalid). User must re-auth."""
    db.query(MetaUserToken).filter(MetaUserToken.user_id == user_id).delete()


def sync_pages(db: Session, user_id: int) -> int:
    """
    Fetch pages from Meta Graph API (/me/accounts) and upsert into meta_pages.
    Uses user access token; stores page tokens encrypted. Returns count of pages synced.
    """
    user_token = _get_user_token(db, user_id)
    url = f"{META_GRAPH_BASE}/me/accounts"
    params = {"access_token": user_token, "fields": "id,name,access_token,category,instagram_business_account"}

    try:
        with httpx.Client() as client:
            resp = client.get(url, params=params)
            if not resp.is_success:
                handle_meta_response(resp, "Facebook pages")
            data = resp.json()
    except TokenInvalidError as e:
        _clear_user_token(db, user_id)
        db.commit()
        raise ValueError(str(e)) from e
    except ValueError:
        raise
    except httpx.RequestError as e:
        raise ValueError("Facebook pages: Request failed. Please try again.") from e
    pages_data = data.get("data") or []
    count = 0
    for p in pages_data:
        page_id = p.get("id")
        page_token = p.get("access_token")
        if not page_id or not page_token:
            continue
        encrypted = encrypt_token(page_token)
        existing = (
            db.query(MetaPage)
            .filter(MetaPage.user_id == user_id, MetaPage.page_id == page_id)
            .first()
        )
        if existing:
            existing.page_name = p.get("name")
            existing.category = p.get("category")
            existing.instagram_business_account_id = (p.get("instagram_business_account") or {}).get("id")
            existing.access_token_encrypted = encrypted

        else:
            db.add(
                MetaPage(
                    user_id=user_id,
                    page_id=page_id,
                    page_name=p.get("name"),
                    category=p.get("category"),
                    instagram_business_account_id=(p.get("instagram_business_account") or {}).get("id"),
                    access_token_encrypted=encrypted,

                )
            )
        count += 1
    AuditService.log_action(
        db,
        action="meta.pages_synced",
        entity_type="meta_page",
        entity_id=None,
        user_id=user_id,
        description=f"Synced {count} Facebook page(s)",
        metadata={"count": count},
    )
    db.commit()
    return count


def list_pages(db: Session, user_id: int) -> List[MetaPage]:
    """Return user's stored pages (no token in model when serialized via schema)."""
    return db.query(MetaPage).filter(MetaPage.user_id == user_id).order_by(MetaPage.page_name).all()


def get_page_token(db: Session, meta_page_id: int, user_id: int) -> str:
    """Return decrypted page access token. Raises ValueError if page not found or not owned by user."""
    page = db.query(MetaPage).filter(MetaPage.id == meta_page_id, MetaPage.user_id == user_id).first()
    if not page:
        raise ValueError("Page not found or not owned by user")
    return decrypt_token(page.access_token_encrypted)


def post_to_page(db: Session, meta_page_id: int, user_id: int, message: str) -> bool:
    """
    Post message to Facebook Page via Graph API. Uses stored page token.
    Returns True on success. Raises on API error.
    """
    post_id = post_to_page_and_get_id(db, meta_page_id, user_id, message)
    return post_id is not None


def post_to_page_and_get_id(db: Session, meta_page_id: int, user_id: int, message: str) -> str | None:
    """
    Post message to Facebook Page via Graph API. Returns the Facebook post id (e.g. page_id_123) on success.
    Raises ValueError on API error (rate limits, invalid token, etc.). TokenInvalidError handled by caller.
    """
    page = db.query(MetaPage).filter(MetaPage.id == meta_page_id, MetaPage.user_id == user_id).first()
    if not page:
        raise ValueError("Page not found or not owned by user")
    token = decrypt_token(page.access_token_encrypted)
    url = f"{META_GRAPH_BASE}/{page.page_id}/feed"
    payload = {"message": message, "access_token": token}
    try:
        with httpx.Client() as client:
            resp = client.post(url, data=payload)
            if not resp.is_success:
                handle_meta_response(resp, "Post to page")
            data = resp.json()
            return data.get("id")
    except TokenInvalidError as e:
        _clear_user_token(db, page.user_id)
        db.commit()
        raise ValueError(str(e)) from e
    except ValueError:
        raise
    except httpx.RequestError as e:
        raise ValueError("Post to page: Request failed. Please try again.") from e


def post_media_to_page_and_get_id(
    db: Session,
    meta_page_id: int,
    user_id: int,
    message: str,
    media_path: str,
    mime_type: str
) -> str | None:
    """
    Post image or video to Facebook Page via Graph API.
    """
    page = db.query(MetaPage).filter(MetaPage.id == meta_page_id, MetaPage.user_id == user_id).first()
    if not page:
        raise ValueError("Page not found or not owned by user")
    
    token = decrypt_token(page.access_token_encrypted)
    
    # Determine endpoint based on mime type
    is_video = mime_type.startswith("video/")
    endpoint = "videos" if is_video else "photos"
    url = f"{META_GRAPH_BASE}/{page.page_id}/{endpoint}"
    
    # Files and data for multipart/form-data
    # For photos, field is 'source'. For videos, it's 'source' too.
    # Caption field is 'caption' for photos and 'description' for videos (usually 'message' works for both on some endpoints, but let's be specific)
    
    files = {"source": open(media_path, "rb")}
    data = {"access_token": token}
    
    if is_video:
        data["description"] = message
    else:
        data["caption"] = message
        
    try:
        with httpx.Client() as client:
            resp = client.post(url, data=data, files=files)
            if not resp.is_success:
                handle_meta_response(resp, f"Post media ({endpoint})")
            res_data = resp.json()
            # Success returns 'id' for photos and 'id' or 'post_id' for videos
            return res_data.get("id") or res_data.get("post_id")
    except TokenInvalidError as e:
        _clear_user_token(db, page.user_id)
        db.commit()
        raise ValueError(str(e)) from e
    except Exception as e:
        raise ValueError(f"Post media failed: {str(e)}")
    finally:
        files["source"].close()
def get_post_insights(db: Session, fb_post_id: str, meta_page_id: int, user_id: int) -> dict:
    """
    Fetch insights for a specific post.
    Metrics: post_impressions_unique (Reach), post_engaged_users (Engagement).
    """
    page = db.query(MetaPage).filter(MetaPage.id == meta_page_id, MetaPage.user_id == user_id).first()
    if not page:
        raise ValueError("Page not found or not owned by user")
    
    token = decrypt_token(page.access_token_encrypted)
    # FB Post IDs are usually PageID_PostID. The Insights API needs the Post ID.
    url = f"{META_GRAPH_BASE}/{fb_post_id}/insights"
    params = {
        "access_token": token,
        "metric": "post_impressions_unique,post_engaged_users"
    }
    
    try:
        with httpx.Client() as client:
            resp = client.get(url, params=params)
            if not resp.is_success:
                handle_meta_response(resp, "Get post insights")
            data = resp.json()
            
            insights = {"reach": 0, "engagement": 0}
            for metric in data.get("data", []):
                name = metric.get("name")
                values = metric.get("values", [])
                if not values:
                    continue
                val = values[0].get("value", 0)
                
                if name == "post_impressions_unique":
                    insights["reach"] = val
                elif name == "post_engaged_users":
                    insights["engagement"] = val
            
            return insights
    except Exception as e:
        raise ValueError(f"Failed to fetch insights: {str(e)}")
