from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.posting_preference import PostingPreference
from app.models.scheduled_post import ScheduledPlatform, ScheduledPost, ScheduledPostStatus

DEFAULT_COOLDOWN_MINUTES = 60
DEFAULT_MAX_POSTS_PER_DAY = 10


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str = ""
    retry_at: datetime | None = None
    error_code: str | None = None


def get_target_limits(db: Session, platform: ScheduledPlatform, target_id: int) -> tuple[int, int]:
    query = db.query(PostingPreference)
    if platform in {ScheduledPlatform.FACEBOOK, ScheduledPlatform.INSTAGRAM}:
        preference = query.filter(PostingPreference.meta_page_id == target_id).first()
    else:
        preference = query.filter(PostingPreference.linkedin_account_id == target_id).first()
    if preference:
        return preference.cooldown_minutes, preference.max_posts_per_day
    return DEFAULT_COOLDOWN_MINUTES, DEFAULT_MAX_POSTS_PER_DAY


def _target_filter(query, platform: ScheduledPlatform, target_id: int):
    query = query.filter(ScheduledPost.platform == platform)
    if platform in {ScheduledPlatform.FACEBOOK, ScheduledPlatform.INSTAGRAM}:
        return query.filter(ScheduledPost.meta_page_id == target_id)
    return query.filter(ScheduledPost.linkedin_account_id == target_id)


def evaluate_target_policy(
    db: Session,
    platform: ScheduledPlatform,
    target_id: int,
    now: datetime | None = None,
) -> PolicyDecision:
    """Enforce cooldown and daily caps for one provider-specific scheduled target."""
    now = now or datetime.now(timezone.utc)
    if not now.tzinfo:
        now = now.replace(tzinfo=timezone.utc)
    cooldown_minutes, max_posts_per_day = get_target_limits(db, platform, target_id)

    last_post = (
        _target_filter(
            db.query(ScheduledPost), platform, target_id
        )
        .filter(
            ScheduledPost.status == ScheduledPostStatus.POSTED,
            ScheduledPost.posted_at.isnot(None),
        )
        .order_by(ScheduledPost.posted_at.desc())
        .first()
    )
    if last_post and last_post.posted_at:
        posted_at = last_post.posted_at
        if not posted_at.tzinfo:
            posted_at = posted_at.replace(tzinfo=timezone.utc)
        cooldown_until = posted_at + timedelta(minutes=cooldown_minutes)
        if cooldown_until > now:
            return PolicyDecision(
                allowed=False,
                reason=f"{platform.value} target cooldown active until {cooldown_until.isoformat()}",
                retry_at=cooldown_until,
                error_code="TARGET_COOLDOWN",
            )

    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)
    posted_today = (
        _target_filter(
            db.query(ScheduledPost), platform, target_id
        )
        .filter(
            ScheduledPost.status == ScheduledPostStatus.POSTED,
            ScheduledPost.posted_at >= day_start,
            ScheduledPost.posted_at < day_end,
        )
        .count()
    )
    if posted_today >= max_posts_per_day:
        return PolicyDecision(
            allowed=False,
            reason=f"Daily {platform.value} limit of {max_posts_per_day} posts reached",
            retry_at=day_end + timedelta(seconds=1),
            error_code="MAX_POSTS_PER_DAY",
        )

    return PolicyDecision(allowed=True)


def evaluate_meta_page_policy(db: Session, meta_page_id: int, now: datetime | None = None) -> PolicyDecision:
    """Backward-compatible Facebook/Instagram wrapper."""
    return evaluate_target_policy(db, ScheduledPlatform.FACEBOOK, meta_page_id, now)
