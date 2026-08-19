from datetime import datetime, timezone, timedelta
from typing import List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.content import Content, ContentStatus
from app.models.meta_page import MetaPage
from app.models.linkedin_account import LinkedInAccount
from app.models.scheduled_post import ScheduledPlatform, ScheduledPost, ScheduledPostStatus
from app.models.posting_preference import PostingPreference
from app.services.audit_service import AuditService
from app.services.publishing_policy import evaluate_target_policy
from app.services.scheduled_execution_service import ScheduledExecutionError, execute_scheduled_post

DEFAULT_COOLDOWN_MINUTES = 60
DEFAULT_MAX_POSTS_PER_DAY = 10


def _owned_target_filter(user_id: int):
    return or_(MetaPage.user_id == user_id, LinkedInAccount.user_id == user_id)


def create_scheduled_post(db: Session, content_id: int, meta_page_id: int, scheduled_at: datetime, user_id: int):
    from app.scheduler import schedule_facebook_post
    return schedule_facebook_post(db, content_id, meta_page_id, scheduled_at, user_id)


def get_scheduled_post(db: Session, scheduled_post_id: int, user_id: int) -> Optional[ScheduledPost]:
    return (
        db.query(ScheduledPost)
        .outerjoin(MetaPage, ScheduledPost.meta_page_id == MetaPage.id)
        .outerjoin(LinkedInAccount, ScheduledPost.linkedin_account_id == LinkedInAccount.id)
        .filter(ScheduledPost.id == scheduled_post_id, _owned_target_filter(user_id))
        .first()
    )


def list_scheduled_posts(
    db: Session,
    user_id: int,
    status: Optional[ScheduledPostStatus] = None,
    meta_page_id: Optional[int] = None,
    linkedin_account_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[ScheduledPost]:
    query = (
        db.query(ScheduledPost)
        .outerjoin(MetaPage, ScheduledPost.meta_page_id == MetaPage.id)
        .outerjoin(LinkedInAccount, ScheduledPost.linkedin_account_id == LinkedInAccount.id)
        .filter(_owned_target_filter(user_id))
    )
    if status is not None:
        query = query.filter(ScheduledPost.status == status)
    if meta_page_id is not None:
        query = query.filter(ScheduledPost.meta_page_id == meta_page_id)
    if linkedin_account_id is not None:
        query = query.filter(ScheduledPost.linkedin_account_id == linkedin_account_id)
    return query.order_by(ScheduledPost.scheduled_at.desc()).offset(skip).limit(limit).all()


def set_posting_preference(
    db: Session,
    meta_page_id: int,
    user_id: int,
    cooldown_minutes: int = DEFAULT_COOLDOWN_MINUTES,
    max_posts_per_day: int = DEFAULT_MAX_POSTS_PER_DAY,
):
    page = db.query(MetaPage).filter(MetaPage.id == meta_page_id, MetaPage.user_id == user_id).first()
    if not page:
        return None
    pref = db.query(PostingPreference).filter(PostingPreference.meta_page_id == meta_page_id).first()
    if not pref:
        pref = PostingPreference(meta_page_id=meta_page_id)
        db.add(pref)
    pref.cooldown_minutes = cooldown_minutes
    pref.max_posts_per_day = max_posts_per_day
    db.commit()
    db.refresh(pref)
    return pref


def set_linkedin_posting_preference(
    db: Session,
    linkedin_account_id: int,
    user_id: int,
    cooldown_minutes: int = DEFAULT_COOLDOWN_MINUTES,
    max_posts_per_day: int = DEFAULT_MAX_POSTS_PER_DAY,
):
    account = db.query(LinkedInAccount).filter(
        LinkedInAccount.id == linkedin_account_id,
        LinkedInAccount.user_id == user_id,
    ).first()
    if not account:
        return None
    pref = db.query(PostingPreference).filter(PostingPreference.linkedin_account_id == linkedin_account_id).first()
    if not pref:
        pref = PostingPreference(linkedin_account_id=linkedin_account_id)
        db.add(pref)
    pref.cooldown_minutes = cooldown_minutes
    pref.max_posts_per_day = max_posts_per_day
    db.commit()
    db.refresh(pref)
    return pref


def get_posting_preference(db: Session, meta_page_id: int, user_id: int):
    page = db.query(MetaPage).filter(MetaPage.id == meta_page_id, MetaPage.user_id == user_id).first()
    if not page:
        return None
    return db.query(PostingPreference).filter(PostingPreference.meta_page_id == meta_page_id).first()


def get_linkedin_posting_preference(db: Session, linkedin_account_id: int, user_id: int):
    account = db.query(LinkedInAccount).filter(
        LinkedInAccount.id == linkedin_account_id,
        LinkedInAccount.user_id == user_id,
    ).first()
    if not account:
        return None
    return db.query(PostingPreference).filter(PostingPreference.linkedin_account_id == linkedin_account_id).first()


def cancel_scheduled_post(db: Session, scheduled_post_id: int, user_id: int) -> bool:
    sp = get_scheduled_post(db, scheduled_post_id, user_id)
    if not sp or sp.status not in {ScheduledPostStatus.PENDING, ScheduledPostStatus.RETRYING}:
        return False
    sp.status = ScheduledPostStatus.CANCELLED
    db.commit()
    return True


def _check_cooldown(db: Session, meta_page_id: int, now: datetime) -> bool:
    return evaluate_target_policy(db, ScheduledPlatform.FACEBOOK, meta_page_id, now).error_code != "TARGET_COOLDOWN"


def _check_max_per_day(db: Session, meta_page_id: int, day_start: datetime) -> bool:
    decision = evaluate_target_policy(db, ScheduledPlatform.FACEBOOK, meta_page_id, day_start)
    return decision.error_code != "MAX_POSTS_PER_DAY"


def process_due_posts(db: Session) -> dict:
    """Synchronous fallback using the same provider-neutral executor as Celery."""
    now = datetime.now(timezone.utc)
    due = db.query(ScheduledPost).filter(
        ScheduledPost.status == ScheduledPostStatus.PENDING,
        ScheduledPost.scheduled_at <= now,
    ).order_by(ScheduledPost.scheduled_at).all()
    posted = failed = skipped = 0
    for sp in due:
        target_id = sp.meta_page_id if sp.platform in {ScheduledPlatform.FACEBOOK, ScheduledPlatform.INSTAGRAM} else sp.linkedin_account_id
        if not target_id:
            sp.status = ScheduledPostStatus.FAILED
            sp.failure_reason = "Scheduled target is missing"
            sp.last_error_code = "INVALID_TARGET"
            failed += 1
            db.commit()
            continue
        policy = evaluate_target_policy(db, sp.platform, target_id, now)
        if not policy.allowed:
            skipped += 1
            continue
        try:
            sp.status = ScheduledPostStatus.PROCESSING
            sp.attempt_count = (sp.attempt_count or 0) + 1
            db.commit()
            execute_scheduled_post(db, sp)
            sp.status = ScheduledPostStatus.POSTED
            sp.posted_at = now
            sp.completed_at = now
            posted += 1
        except ScheduledExecutionError as exc:
            sp.status = ScheduledPostStatus.FAILED
            sp.failure_reason = str(exc)[:512]
            sp.last_error_code = exc.error_code
            sp.completed_at = now
            failed += 1
        db.commit()
    return {"posted": posted, "failed": failed, "skipped": skipped}
