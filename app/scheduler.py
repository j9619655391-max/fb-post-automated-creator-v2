"""
Celery-based scheduler for Facebook post publishing.

- schedule_facebook_post(db, content_id, meta_page_id, publish_time): creates ScheduledPost and
  enqueues publish_to_facebook_task to run at publish_time.
- publish_to_facebook_task(scheduled_post_id): Celery task that posts content to the page and
  updates status (PROCESSING -> POSTED or FAILED).

Requires Redis running and Celery worker: celery -A app.scheduler worker -l info
"""
from datetime import datetime, timedelta, timezone
import logging

from celery import Celery
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.content import Content
from app.models.scheduled_post import ScheduledPost, ScheduledPostStatus, ScheduledPlatform
from app.models.meta_page import MetaPage
from app.models.linkedin_account import LinkedInAccount
from app.services.audit_service import AuditService
from app.services.publish_errors import classify_publish_failure
from app.services.scheduled_execution_service import ScheduledExecutionError, execute_scheduled_post
from app.services.ai_provider_health_service import collect_ai_provider_health

logger = logging.getLogger(__name__)

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


def schedule_post(
    db: Session,
    content_id: int,
    platform: ScheduledPlatform,
    scheduled_at: datetime,
    user_id: int,
    *,
    meta_page_id: int | None = None,
    linkedin_account_id: int | None = None,
):
    """Create one provider-neutral scheduled target and enqueue its executor."""
    from app.models.content import ContentStatus

    content = db.query(Content).filter(Content.id == content_id).first()
    if not content or content.status != ContentStatus.APPROVED:
        return None
    scheduled_at = scheduled_at if scheduled_at.tzinfo else scheduled_at.replace(tzinfo=timezone.utc)
    if scheduled_at <= datetime.now(timezone.utc):
        return None

    if platform in {ScheduledPlatform.FACEBOOK, ScheduledPlatform.INSTAGRAM}:
        target = db.query(MetaPage).filter(MetaPage.id == meta_page_id, MetaPage.user_id == user_id).first()
        if not target:
            return None
        target_id = meta_page_id
    elif platform == ScheduledPlatform.LINKEDIN:
        target = db.query(LinkedInAccount).filter(
            LinkedInAccount.id == linkedin_account_id,
            LinkedInAccount.user_id == user_id,
        ).first()
        if not target:
            return None
        target_id = linkedin_account_id
    else:
        return None

    idempotency_key = f"{platform.value}:{content_id}:{target_id}:{scheduled_at.isoformat()}"
    existing = db.query(ScheduledPost).filter(
        ScheduledPost.idempotency_key == idempotency_key,
        ScheduledPost.status.in_([
            ScheduledPostStatus.PENDING,
            ScheduledPostStatus.PROCESSING,
            ScheduledPostStatus.RETRYING,
        ]),
    ).first()
    if existing:
        return existing

    sp = ScheduledPost(
        content_id=content_id,
        platform=platform,
        meta_page_id=meta_page_id,
        linkedin_account_id=linkedin_account_id,
        scheduled_at=scheduled_at,
        status=ScheduledPostStatus.PENDING,
        idempotency_key=idempotency_key,
    )
    db.add(sp)
    db.commit()
    db.refresh(sp)
    publish_scheduled_post_task.apply_async(args=[sp.id], eta=scheduled_at)
    return sp


def schedule_facebook_post(db: Session, content_id: int, meta_page_id: int, publish_time: datetime, user_id: int):
    """Backward-compatible Facebook scheduling wrapper."""
    return schedule_post(
        db, content_id, ScheduledPlatform.FACEBOOK, publish_time, user_id, meta_page_id=meta_page_id
    )


def schedule_linkedin_post(db: Session, content_id: int, linkedin_account_id: int, publish_time: datetime, user_id: int):
    """Schedule approved content for a LinkedIn account."""
    return schedule_post(
        db, content_id, ScheduledPlatform.LINKEDIN, publish_time, user_id, linkedin_account_id=linkedin_account_id
    )


@celery_app.task(
    bind=True,
    name="app.publish_scheduled_post_task",
    max_retries=5,
    acks_late=True,
)
def publish_scheduled_post_task(self, scheduled_post_id: int):
    """Execute one provider-neutral scheduled target with bounded retries."""
    db = SessionLocal()
    try:
        sp = db.query(ScheduledPost).filter(ScheduledPost.id == scheduled_post_id).first()
        if not sp:
            return {"ok": False, "reason": "ScheduledPost not found"}
        if sp.status in [ScheduledPostStatus.POSTED, ScheduledPostStatus.CANCELLED, ScheduledPostStatus.DEAD_LETTER]:
            return {"ok": True, "status": sp.status.value}

        sp.status = ScheduledPostStatus.PROCESSING
        sp.attempt_count = (sp.attempt_count or 0) + 1
        sp.next_retry_at = None
        db.commit()
        logger.info(
            "scheduled_post.processing",
            extra={
                "scheduled_post_id": sp.id,
                "platform": sp.platform.value,
                "attempt": sp.attempt_count,
            },
        )

        try:
            execute_scheduled_post(db, sp)
            sp.status = ScheduledPostStatus.POSTED
            sp.posted_at = datetime.now(timezone.utc)
            sp.failure_reason = None
            sp.completed_at = sp.posted_at
            db.commit()
            logger.info(
                "scheduled_post.posted",
                extra={"scheduled_post_id": sp.id, "platform": sp.platform.value},
            )
            return {"ok": True, "status": "posted", "platform": sp.platform.value}
        except ScheduledExecutionError as exc:
            classification = classify_publish_failure(exc)
            if exc.error_code in {"TARGET_COOLDOWN", "MAX_POSTS_PER_DAY"}:
                classification = classification.__class__(exc.error_code, True, str(exc))
            if not classification.retryable:
                sp.status = ScheduledPostStatus.FAILED
                sp.last_error_code = exc.error_code or classification.code
                sp.failure_reason = str(exc)[:512]
                sp.completed_at = datetime.now(timezone.utc)
                sp.next_retry_at = None
                db.commit()
                logger.warning(
                    "scheduled_post.failed_terminal",
                    extra={
                        "scheduled_post_id": sp.id,
                        "platform": sp.platform.value,
                        "error_code": sp.last_error_code,
                    },
                )
                return {"ok": False, "status": "failed", "reason": sp.failure_reason}

            if self.request.retries >= self.max_retries:
                sp.status = ScheduledPostStatus.DEAD_LETTER
                sp.last_error_code = exc.error_code or classification.code
                sp.failure_reason = str(exc)[:512]
                sp.completed_at = datetime.now(timezone.utc)
                sp.next_retry_at = None
                db.commit()
                logger.error(
                    "scheduled_post.dead_letter",
                    extra={
                        "scheduled_post_id": sp.id,
                        "platform": sp.platform.value,
                        "error_code": sp.last_error_code,
                    },
                )
                return {"ok": False, "status": "dead_letter", "reason": sp.failure_reason}

            delay = min(
                86400,
                max(1, int((exc.retry_at - datetime.now(timezone.utc)).total_seconds()))
                if exc.retry_at else min(3600, 2 ** max(0, self.request.retries)),
            )
            sp.status = ScheduledPostStatus.RETRYING
            sp.last_error_code = exc.error_code or classification.code
            sp.failure_reason = str(exc)[:512]
            sp.next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=delay)
            db.commit()
            logger.warning(
                "scheduled_post.retrying",
                extra={
                    "scheduled_post_id": sp.id,
                    "platform": sp.platform.value,
                    "error_code": sp.last_error_code,
                    "retry_delay_seconds": delay,
                },
            )
            raise self.retry(exc=exc, countdown=delay)
        except Exception as exc:
            classification = classify_publish_failure(exc)
            if not classification.retryable:
                sp.status = ScheduledPostStatus.FAILED
                sp.last_error_code = classification.code
                sp.failure_reason = classification.message[:512]
                sp.completed_at = datetime.now(timezone.utc)
                sp.next_retry_at = None
                db.commit()
                logger.warning(
                    "scheduled_post.failed_terminal",
                    extra={
                        "scheduled_post_id": sp.id,
                        "platform": sp.platform.value,
                        "error_code": sp.last_error_code,
                    },
                )
                return {"ok": False, "status": "failed", "reason": classification.message}
            if self.request.retries >= self.max_retries:
                sp.status = ScheduledPostStatus.DEAD_LETTER
                sp.last_error_code = classification.code
                sp.failure_reason = classification.message[:512]
                sp.completed_at = datetime.now(timezone.utc)
                sp.next_retry_at = None
                db.commit()
                logger.error(
                    "scheduled_post.dead_letter",
                    extra={
                        "scheduled_post_id": sp.id,
                        "platform": sp.platform.value,
                        "error_code": sp.last_error_code,
                    },
                )
                return {"ok": False, "status": "dead_letter", "reason": classification.message}
            delay = min(3600, 2 ** max(0, self.request.retries))
            sp.status = ScheduledPostStatus.RETRYING
            sp.last_error_code = classification.code
            sp.failure_reason = classification.message[:512]
            sp.next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=delay)
            db.commit()
            raise self.retry(exc=exc, countdown=delay)
    finally:
        db.close()


# Backward-compatible symbol for existing imports and tests.
publish_to_facebook_task = publish_scheduled_post_task


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

@celery_app.task(name="app.ai_provider_health_task")
def ai_provider_health_task():
    """Log safe provider health alerts; this task performs no provider API calls."""
    db = SessionLocal()
    try:
        result = collect_ai_provider_health(db)
        if result["alert"]:
            logger.warning(
                "ai_provider.alert",
                extra={
                    "provider": result["provider"],
                    "failed_jobs": result["failed_jobs"],
                    "retrying_plans": result["retrying_plans"],
                    "alert_reason": result["alert_reason"],
                },
            )
        return result
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
    "check-ai-provider-health": {
        "task": "app.ai_provider_health_task",
        "schedule": 900.0, # 15 minutes
    },

}
