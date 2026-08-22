"""
Facebook & Instagram Graph API integration: publish content to Facebook Pages and Instagram.

OAuth 2.0 flow for Facebook login is handled by:
- app.api.routes.auth_facebook (login, callback, disconnect)
- app.services.facebook_oauth_service (authorize URL, exchange code, store token)

This module provides:
  - publish_to_facebook(content) - multi-page Facebook publishing
  - publish_to_instagram(content) - Instagram publishing via container creation & publish
"""
from typing import Optional, List
import time

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.meta_api_errors import TokenInvalidError

from app.models.content import Content
from app.models.meta_page import MetaPage
from app.models.content_execution import ContentPublishStatus, PublishStatusEnum
from app.services.facebook_pages_service import post_to_page_and_get_id
from app.services.publish_errors import classify_publish_failure


def publish_to_facebook(
    db: Session,
    content_id: int,
    meta_page_ids: list[int],
    user_id: int,
) -> Content:
    """
    Publish content to multiple Facebook Pages via Graph API automatically.

    - Builds message from content title + body.
    - Posts to Page feeds; updates individual ContentPublishStatus records.
    - Gracefully handles individual page failures.

    Raises:
        ValueError: Content not found, or not approved.
    """
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise ValueError("Content not found")

    if content.status != "approved":
        raise ValueError("Content must be APPROVED to publish to Facebook")

    message = f"{content.title}\n\n{content.body}"

    for meta_page_id in meta_page_ids:
        page = db.query(MetaPage).filter(MetaPage.id == meta_page_id, MetaPage.user_id == user_id).first()
        if not page:
            continue # Skip invalid pages

        existing_status = (
            db.query(ContentPublishStatus)
            .filter(
                ContentPublishStatus.content_id == content.id,
                ContentPublishStatus.meta_page_id == meta_page_id,
            )
            .order_by(ContentPublishStatus.id.desc())
            .first()
        )
        if existing_status and existing_status.status in (
            PublishStatusEnum.POSTED,
            PublishStatusEnum.PROCESSING,
        ):
            continue

        publish_status = ContentPublishStatus(
            content_id=content.id,
            meta_page_id=meta_page_id,
            status=PublishStatusEnum.PROCESSING
        )
        db.add(publish_status)
        db.commit()

        try:
            if content.media_id:
                from app.services.facebook_pages_service import post_media_to_page_and_get_id
                platform_post_id = post_media_to_page_and_get_id(
                    db, 
                    meta_page_id, 
                    user_id, 
                    message, 
                    content.media.stored_path, 
                    content.media.mime_type
                )
            else:
                platform_post_id = post_to_page_and_get_id(db, meta_page_id, user_id, message)
            
            publish_status.platform_post_id = platform_post_id
            publish_status.status = PublishStatusEnum.POSTED
        except TokenInvalidError as e:
            publish_status.status = PublishStatusEnum.FAILED
            publish_status.error_message = "AUTH_REQUIRED: Facebook connection expired or invalid. Please reconnect."
        except ValueError as e:
            classification = classify_publish_failure(e)
            publish_status.status = PublishStatusEnum.FAILED
            publish_status.error_message = f"{classification.code}: {classification.message}"
        except Exception as e:
            classification = classify_publish_failure(e)
            publish_status.status = PublishStatusEnum.FAILED
            publish_status.error_message = f"{classification.code}: {classification.message}"
            
        db.commit()

    db.refresh(content)
    return content


def publish_to_instagram(
    db: Session,
    content_id: int,
    meta_page_id: int,
    user_id: int,
    image_url: str,
) -> dict:
    """
    Publish an image post to Instagram Business Account linked to a Facebook Page.

    Flow (Instagram Graph API):
      1. GET /page_id?fields=instagram_business_account to retrieve IG account ID.
      2. POST /{ig_account_id}/media to create a media container.
      3. POST /{ig_account_id}/media_publish to publish the container.

    Args:
        db: Database session.
        content_id: ID of the Content record.
        meta_page_id: ID of the MetaPage (linked to a Facebook Page).
        user_id: ID of the authenticated user.
        image_url: Publicly accessible URL of the image to post.

    Returns:
        dict with 'ig_media_id' on success.

    Raises:
        ValueError: If the page, content, or IG account is not found, or API fails.
    """
    import httpx

    META_GRAPH_BASE = "https://graph.facebook.com/v18.0"

    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise ValueError("Content not found")

    page = db.query(MetaPage).filter(MetaPage.id == meta_page_id, MetaPage.user_id == user_id).first()
    if not page:
        raise ValueError("Page not found or not owned by user")

    from app.core.token_crypto import decrypt_token
    page_token = decrypt_token(page.access_token_encrypted)

    caption = f"{content.title}\n\n{content.body}"

    with httpx.Client(timeout=30.0) as client:
        # Step 1 – Use persisted linkage, refreshing it read-only if absent.
        ig_id = page.instagram_business_account_id
        if not ig_id:
            page_resp = client.get(
                f"{META_GRAPH_BASE}/{page.page_id}",
                params={"fields": "instagram_business_account", "access_token": page_token},
            )
            if not page_resp.is_success:
                raise ValueError(f"Failed to fetch Instagram account for page: {page_resp.text}")
            page_data = page_resp.json()
            ig_id = (page_data.get("instagram_business_account") or {}).get("id")
            if ig_id:
                page.instagram_business_account_id = ig_id
                db.commit()
        if not ig_id:
            raise ValueError("No Instagram Business Account linked to this Facebook Page.")

        # Step 2 – Check Meta's rolling 24-hour publishing quota before
        # creating a container. This prevents avoidable containers when the
        # provider quota is already exhausted.
        limit_resp = client.get(
            f"{META_GRAPH_BASE}/{ig_id}/content_publishing_limit",
            params={
                "fields": "quota_usage,config",
                "since": int(time.time()) - 86400,
                "access_token": page_token,
            },
        )
        if not limit_resp.is_success:
            raise ValueError(f"Instagram publishing rate-limit check failed: {limit_resp.text}")
        limit_data = limit_resp.json().get("data") or []
        if limit_data:
            usage_data = limit_data[0] or {}
            quota_usage = int(usage_data.get("quota_usage") or 0)
            quota_total = int((usage_data.get("config") or {}).get("quota_total") or 0)
            if quota_total and quota_usage >= quota_total:
                raise ValueError(
                    f"Instagram publishing rate limit reached ({quota_usage}/{quota_total} containers in 24 hours)"
                )

        # Step 3 – Create media container
        container_resp = client.post(

            f"{META_GRAPH_BASE}/{ig_id}/media",
            params={
                "image_url": image_url,
                "caption": caption,
                "access_token": page_token,
            },
        )
        if not container_resp.is_success:
            raise ValueError(f"Instagram media container creation failed: {container_resp.text}")

        container_id = container_resp.json().get("id")
        if not container_id:
            raise ValueError("No container ID returned from Instagram API.")

        # Step 4 – Poll container readiness before publishing. Meta documents
        # FINISHED/PUBLISHED as publishable terminal states and recommends a
        # bounded status check rather than immediately calling media_publish.
        poll_attempts = max(1, settings.instagram_container_poll_attempts)
        poll_interval = max(0.0, settings.instagram_container_poll_interval_seconds)
        terminal_status = None
        for attempt in range(poll_attempts):
            status_resp = client.get(
                f"{META_GRAPH_BASE}/{container_id}",
                params={"fields": "status_code,status", "access_token": page_token},
            )
            if not status_resp.is_success:
                raise ValueError(f"Instagram media container status check failed: {status_resp.text}")
            status_data = status_resp.json()
            status_code = str(status_data.get("status_code") or "").upper()
            if status_code in {"FINISHED", "PUBLISHED"}:
                terminal_status = status_code
                break
            if status_code in {"ERROR", "EXPIRED"}:
                detail = status_data.get("status") or status_code
                raise ValueError(f"Instagram media container is not publishable ({status_code}): {detail}")
            if status_code != "IN_PROGRESS":
                raise ValueError(f"Instagram media container returned unknown status: {status_code or 'EMPTY'}")
            if attempt < poll_attempts - 1 and poll_interval:
                time.sleep(poll_interval)

        if terminal_status is None:
            raise ValueError(
                f"Instagram media container remained IN_PROGRESS after {poll_attempts} status checks"
            )

        # Step 5 – Publish the media container.
        publish_resp = client.post(
            f"{META_GRAPH_BASE}/{ig_id}/media_publish",
            params={"creation_id": container_id, "access_token": page_token},
        )

        if not publish_resp.is_success:
            raise ValueError(f"Instagram media publish failed: {publish_resp.text}")

        ig_media_id = publish_resp.json().get("id")

    return {"ig_media_id": ig_media_id}
