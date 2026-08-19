"""
Celery-based scheduler for Facebook post publishing.

- schedule_facebook_post(db, content_id, meta_page_id, publish_time): creates ScheduledPost and
  enqueues publish_to_facebook_task to run at publish_time.
- publish_to_facebook_task(scheduled_post_id): Celery task that posts content to the page and
  updates status (PROCESSING -> POSTED or FAILED).

Requires Redis running and Celery worker: celery -A app.scheduler worker -l info
"""
from datetime import datetime, timedelta, timezone

from celery import Celery
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.content import Content
from app.models.scheduled_post import ScheduledPost, ScheduledPostStatus
from app.models.meta_page import MetaPage
from app.models.content_execution import ContentPublishStatus, PublishStatusEnum
from app.services.facebook_pages_service import post_to_page_and_get_id
from app.services.audit_service import AuditService
from app.services.publishing_policy import evaluate_meta_page_policy
from app.services.publish_errors import classify_publish_failure

celery_app = Celery(
    "fb_scheduler",
    broker=settings.celery_broker_url,
    backend=settings.celery_broker_url,
)
celery_app.conf.update(
    timezone="UTC",
    enable_utc=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
)


def schedule_facebook_post(
    db: Session,
    content_id: int,
    meta_page_id: int,
    publish_time: datetime,
    user_id: int,
):
    """
    Create a ScheduledPost and enqueue a Celery task to publish at publish_time.
    Content must be APPROVED; page must belong to user.
    Returns ScheduledPost or None if validation fails.
    """
    from app.models.content import ContentStatus

    content = db.query(Content).filter(Content.id == content_id).first()
    if not content or content.status != ContentStatus.APPROVED:
        return None

    scheduled_at = publish_time if publish_time.tzinfo else publish_time.replace(tzinfo=timezone.utc)
    if scheduled_at <= datetime.now(timezone.utc):
        return None

    page = db.query(MetaPage).filter(MetaPage.id == meta_page_id, MetaPage.user_id == user_id).first()
    if not page:
        return None

    # Avoid duplicate queue entries when approval is retried or a client submits
    # the same scheduling request more than once.
    idempotency_key = f"facebook:{content_id}:{meta_page_id}:{scheduled_at.isoformat()}"
    existing = (
        db.query(ScheduledPost)
        .filter(
            ScheduledPost.idempotency_key == idempotency_key,
            ScheduledPost.status.in_([
                ScheduledPostStatus.PENDING,
                ScheduledPostStatus.PROCESSING,
                ScheduledPostStatus.RETRYING,
            ]),
        )
        .first()
    )
    if existing:
        return existing

    sp = ScheduledPost(
        content_id=content_id,
        meta_page_id=meta_page_id,
        scheduled_at=scheduled_at,
        status=ScheduledPostStatus.PENDING,
        idempotency_key=idempotency_key,
    )
    db.add(sp)
    db.commit()
    db.refresh(sp)
    publish_to_facebook_task.apply_async(
        args=[sp.id],
        eta=scheduled_at,
    )
    return sp


@celery_app.task(
    bind=True,
    name="app.publish_to_facebook_task",
    max_retries=5,
    acks_late=True,
)
def publish_to_facebook_task(self, scheduled_post_id: int):
    """
    Celery task: load ScheduledPost, set PROCESSING, post to Facebook via fb_api service.
    """
    from app.services.fb_api import publish_to_facebook
    
    db = SessionLocal()
    try:
        sp = db.query(ScheduledPost).filter(ScheduledPost.id == scheduled_post_id).first()
        if not sp:
            return {"ok": False, "reason": "ScheduledPost not found"}
        
        # If already posted or failed after retries, skip
        if sp.status in [
            ScheduledPostStatus.POSTED,
            ScheduledPostStatus.CANCELLED,
            ScheduledPostStatus.DEAD_LETTER,
        ]:
            return {"ok": True, "status": sp.status.value}

        policy = evaluate_meta_page_policy(db, sp.meta_page_id)
        if not policy.allowed:
            sp.status = ScheduledPostStatus.RETRYING
            sp.last_error_code = policy.error_code
            sp.failure_reason = policy.reason[:512]
            sp.next_retry_at = policy.retry_at
            db.commit()
            countdown = (
                max(1, int((policy.retry_at - datetime.now(timezone.utc)).total_seconds()))
                if policy.retry_at else 60
            )
            raise self.retry(
                exc=RuntimeError(policy.reason),
                countdown=min(countdown, 86400),
            )

        sp.status = ScheduledPostStatus.PROCESSING
        sp.attempt_count = (sp.attempt_count or 0) + 1
        sp.next_retry_at = None
        db.commit()

        try:
            # Use the unified publish_to_facebook service (handles text/media)
            publish_to_facebook(
                db=db,
                content_id=sp.content_id,
                meta_page_ids=[sp.meta_page_id],
                user_id=sp.meta_page.user_id,
            )

            # The unified publisher records per-target failures and may return
            # normally even when the target failed. Do not mark the parent job
            # as POSTED unless the latest target execution succeeded.
            target_status = (
                db.query(ContentPublishStatus)
                .filter(
                    ContentPublishStatus.content_id == sp.content_id,
                    ContentPublishStatus.meta_page_id == sp.meta_page_id,
                )
                .order_by(ContentPublishStatus.id.desc())
                .first()
            )
            if not target_status or target_status.status != PublishStatusEnum.POSTED:
                sp.status = ScheduledPostStatus.FAILED
                sp.last_error_code = "PUBLISH_FAILED"
                sp.failure_reason = (
                    target_status.error_message
                    if target_status and target_status.error_message
                    else "Facebook target publishing failed"
                )[:512]
                sp.completed_at = datetime.now(timezone.utc)
                db.commit()
                return {
                    "ok": False,
                    "status": "failed",
                    "reason": sp.failure_reason,
                }
            
            sp.status = ScheduledPostStatus.POSTED
            sp.posted_at = datetime.now(timezone.utc)
            sp.failure_reason = None
            sp.completed_at = sp.posted_at
            db.commit()
            return {"ok": True, "status": "posted"}
            
        except Exception as e:
            classification = classify_publish_failure(e)
            if not classification.retryable:
                sp.status = ScheduledPostStatus.FAILED
                sp.last_error_code = classification.code
                sp.failure_reason = classification.message[:512]
                sp.completed_at = datetime.now(timezone.utc)
                sp.next_retry_at = None
                db.commit()
                return {"ok": False, "status": "failed", "reason": classification.message}

            if self.request.retries >= self.max_retries:
                sp.status = ScheduledPostStatus.DEAD_LETTER
                sp.last_error_code = classification.code
                sp.failure_reason = classification.message[:512]
                sp.completed_at = datetime.now(timezone.utc)
                sp.next_retry_at = None
                db.commit()
                return {"ok": False, "status": "dead_letter", "reason": classification.message}

            delay = min(3600, 2 ** max(0, self.request.retries))
            sp.status = ScheduledPostStatus.RETRYING
            sp.last_error_code = classification.code
            sp.failure_reason = classification.message[:512]
            sp.next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=delay)
            db.commit()
            raise self.retry(exc=e, countdown=delay)
            
    finally:
        db.close()


@celery_app.task(name="app.token_guard_task")
def token_guard_task():
    """
    Periodic task: Check all MetaUserTokens for expiration and log warnings.
    """
    from app.models.meta_oauth import MetaUserToken
    from app.services.audit_service import AuditService
    from datetime import timedelta
    
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        warning_threshold = now + timedelta(days=7)
        
        tokens = db.query(MetaUserToken).all()
        results = {"checked": len(tokens), "warning": 0, "expired": 0}
        
        for t in tokens:
            if not t.expires_at:
                continue
                
            # Ensure expires_at is timezone-aware for comparison
            expires_at = t.expires_at
            if not expires_at.tzinfo:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
                
            if expires_at < now:
                results["expired"] += 1
                AuditService.log_action(
                    db, "token.expired", "user", t.user_id, t.user_id,
                    f"Meta access token for user {t.user_id} has expired.",
                    {"expires_at": expires_at.isoformat()}
                )
            elif expires_at < warning_threshold:
                results["warning"] += 1
                from app.services.facebook_oauth_service import refresh_long_lived_token
                # Attempt to refresh
                refreshed = refresh_long_lived_token(db, t)
                if not refreshed:
                    # If refresh failed, still log warning for manual intervention
                    AuditService.log_action(
                        db, "token.warning", "user", t.user_id, t.user_id,
                        f"Meta access token for user {t.user_id} expires soon and auto-refresh failed.",
                        {"expires_at": expires_at.isoformat()}
                    )
        
        db.commit()
        return results
    finally:
        db.close()

@celery_app.task(name="app.run_due_generation_plans_task")
def run_due_generation_plans_task():
    """Create due AI drafts from active plans; publishing still requires approval."""
    from app.services.generation_plan_service import run_due_plans

    db = SessionLocal()
    try:
        return run_due_plans(db)
    finally:
        db.close()


# Periodic task schedule
celery_app.conf.beat_schedule = {
    "run-due-generation-plans": {
        "task": "app.run_due_generation_plans_task",
        "schedule": 300.0,
    },
    "check-tokens-daily": {
        "task": "app.token_guard_task",
        "schedule": 86400.0, # 24 hours
    },
}
