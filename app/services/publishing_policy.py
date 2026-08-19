from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.posting_preference import PostingPreference
from app.models.scheduled_post import ScheduledPost, ScheduledPostStatus

DEFAULT_COOLDOWN_MINUTES = 60
DEFAULT_MAX_POSTS_PER_DAY = 10


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str = ""
    retry_at: datetime | None = None
    error_code: str | None = None


def get_meta_page_limits(db: Session, meta_page_id: int) -> tuple[int, int]:
    preference = db.query(PostingPreference).filter(PostingPreference.meta_page_id == meta_page_id).first()
    if preference:
        return preference.cooldown_minutes, preference.max_posts_per_day
    return DEFAULT_COOLDOWN_MINUTES, DEFAULT_MAX_POSTS_PER_DAY


def evaluate_meta_page_policy(db: Session, meta_page_id: int, now: datetime | None = None) -> PolicyDecision:
    """Enforce page cooldown and daily cap for Facebook/Instagram Meta-page posts."""
    now = now or datetime.now(timezone.utc)
    if not now.tzinfo:
        now = now.replace(tzinfo=timezone.utc)
    cooldown_minutes, max_posts_per_day = get_meta_page_limits(db, meta_page_id)

    last_post = (
        db.query(ScheduledPost)
        .filter(
            ScheduledPost.meta_page_id == meta_page_id,
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
                reason=f"Page cooldown active until {cooldown_until.isoformat()}",
                retry_at=cooldown_until,
                error_code="PAGE_COOLDOWN",
            )

    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)
    posted_today = (
        db.query(ScheduledPost)
        .filter(
            ScheduledPost.meta_page_id == meta_page_id,
            ScheduledPost.status == ScheduledPostStatus.POSTED,
            ScheduledPost.posted_at >= day_start,
            ScheduledPost.posted_at < day_end,
        )
        .count()
    )
    if posted_today >= max_posts_per_day:
        return PolicyDecision(
            allowed=False,
            reason=f"Daily page limit of {max_posts_per_day} posts reached",
            retry_at=day_end + timedelta(seconds=1),
            error_code="MAX_POSTS_PER_DAY",
        )

    return PolicyDecision(allowed=True)
