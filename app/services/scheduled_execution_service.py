from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.content import Content, ContentStatus
from app.models.content_execution import ContentPublishStatus, PublishStatusEnum
from app.models.scheduled_post import ScheduledPlatform, ScheduledPost
from app.services import fb_api, linkedin_api
from app.services.publishing_policy import evaluate_target_policy
from app.services.storage import get_storage_provider


class ScheduledExecutionError(RuntimeError):
    def __init__(self, message: str, error_code: str = "SCHEDULED_EXECUTION_FAILED", retry_at=None):
        super().__init__(message)
        self.error_code = error_code
        self.retry_at = retry_at


def _target_id(scheduled_post: ScheduledPost) -> int:
    if scheduled_post.platform in {ScheduledPlatform.FACEBOOK, ScheduledPlatform.INSTAGRAM}:
        if not scheduled_post.meta_page_id:
            raise ScheduledExecutionError("Meta target is missing", "INVALID_TARGET")
        return scheduled_post.meta_page_id
    if not scheduled_post.linkedin_account_id:
        raise ScheduledExecutionError("LinkedIn target is missing", "INVALID_TARGET")
    return scheduled_post.linkedin_account_id


def _target_user_id(scheduled_post: ScheduledPost) -> int:
    if scheduled_post.platform in {ScheduledPlatform.FACEBOOK, ScheduledPlatform.INSTAGRAM}:
        if not scheduled_post.meta_page:
            raise ScheduledExecutionError("Meta target was not found", "INVALID_TARGET")
        return scheduled_post.meta_page.user_id
    if not scheduled_post.linkedin_account:
        raise ScheduledExecutionError("LinkedIn target was not found", "INVALID_TARGET")
    return scheduled_post.linkedin_account.user_id


def _latest_execution(db: Session, scheduled_post: ScheduledPost) -> ContentPublishStatus | None:
    query = db.query(ContentPublishStatus).filter(ContentPublishStatus.content_id == scheduled_post.content_id)
    if scheduled_post.platform in {ScheduledPlatform.FACEBOOK, ScheduledPlatform.INSTAGRAM}:
        query = query.filter(ContentPublishStatus.meta_page_id == scheduled_post.meta_page_id)
    else:
        query = query.filter(ContentPublishStatus.linkedin_account_id == scheduled_post.linkedin_account_id)
    return query.order_by(ContentPublishStatus.id.desc()).first()


def execute_scheduled_post(db: Session, scheduled_post: ScheduledPost) -> None:
    """Execute one scheduled target and raise on a target-level failure."""
    content = db.query(Content).filter(Content.id == scheduled_post.content_id).first()
    if not content:
        raise ScheduledExecutionError("Content not found", "CONTENT_NOT_FOUND")
    if content.status != ContentStatus.APPROVED:
        raise ScheduledExecutionError("Content must be APPROVED to publish", "INVALID_CONTENT")

    target_id = _target_id(scheduled_post)
    policy = evaluate_target_policy(db, scheduled_post.platform, target_id)
    if not policy.allowed:
        raise ScheduledExecutionError(policy.reason, policy.error_code or "TARGET_POLICY", policy.retry_at)

    user_id = _target_user_id(scheduled_post)
    if scheduled_post.platform == ScheduledPlatform.FACEBOOK:
        fb_api.publish_to_facebook(db, scheduled_post.content_id, [target_id], user_id)
    elif scheduled_post.platform == ScheduledPlatform.INSTAGRAM:
        if not content.media:
            raise ScheduledExecutionError(
                "Instagram scheduled publishing requires image media",
                "INVALID_CONTENT",
            )
        image_url = get_storage_provider().get_public_url(content.media.stored_path)
        fb_api.publish_to_instagram(db, scheduled_post.content_id, target_id, user_id, image_url)
    elif scheduled_post.platform == ScheduledPlatform.LINKEDIN:
        linkedin_api.publish_to_linkedin(db, scheduled_post.content_id, [target_id], user_id)

    latest = _latest_execution(db, scheduled_post)
    if not latest or latest.status != PublishStatusEnum.POSTED:
        message = latest.error_message if latest and latest.error_message else "Target publisher failed"
        code = "PUBLISH_FAILED"
        if latest and latest.error_message and ":" in latest.error_message:
            code = latest.error_message.split(":", 1)[0].strip()[:100]
        raise ScheduledExecutionError(message, code)
