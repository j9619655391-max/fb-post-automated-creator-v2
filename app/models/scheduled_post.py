import enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class ScheduledPlatform(str, enum.Enum):
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"


class ScheduledPostStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    POSTED = "posted"
    CANCELLED = "cancelled"
    FAILED = "failed"
    RETRYING = "retrying"
    PARTIALLY_FAILED = "partially_failed"
    DEAD_LETTER = "dead_letter"


class ScheduledPost(Base):
    """Approved content scheduled for a provider-specific social target."""

    __tablename__ = "scheduled_posts"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("content.id"), nullable=False, index=True)
    platform = Column(Enum(ScheduledPlatform), default=ScheduledPlatform.FACEBOOK, nullable=False, index=True)
    meta_page_id = Column(Integer, ForeignKey("meta_pages.id"), nullable=True, index=True)
    linkedin_account_id = Column(Integer, ForeignKey("linkedin_accounts.id"), nullable=True, index=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=False, index=True)
    status = Column(Enum(ScheduledPostStatus), default=ScheduledPostStatus.PENDING, nullable=False, index=True)
    posted_at = Column(DateTime(timezone=True), nullable=True)
    failure_reason = Column(String(512), nullable=True)
    attempt_count = Column(Integer, nullable=False, default=0)
    last_error_code = Column(String(100), nullable=True)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    idempotency_key = Column(String(255), nullable=True, unique=True, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    content = relationship("Content", backref="scheduled_posts")
    meta_page = relationship("MetaPage", backref="scheduled_posts")
    linkedin_account = relationship("LinkedInAccount", backref="scheduled_posts")

    @property
    def provider_label(self) -> str:
        return self.platform.value.title() if self.platform else "Unknown"

    @property
    def retryable(self) -> bool:
        return self.last_error_code in {
            "RATE_LIMIT",
            "NETWORK_ERROR",
            "PROVIDER_5XX",
            "UNKNOWN_PROVIDER_ERROR",
        }

    @property
    def recovery_action(self) -> str | None:
        if self.status not in {ScheduledPostStatus.FAILED, ScheduledPostStatus.DEAD_LETTER}:
            return None
        if self.last_error_code in {"AUTH_REQUIRED", "PERMISSION_DENIED"}:
            return "reauthenticate"
        if self.retryable:
            return "retry"
        if self.last_error_code in {"TARGET_COOLDOWN", "MAX_POSTS_PER_DAY"}:
            return "review_policy"
        return "review"

    @property
    def recovery_hint(self) -> str | None:
        hints = {
            "AUTH_REQUIRED": "Reconnect the provider account before retrying.",
            "PERMISSION_DENIED": "Check provider permissions and reconnect the account if needed.",
            "RATE_LIMIT": "The provider rate limit was reached; retry after the backoff window.",
            "NETWORK_ERROR": "The provider could not be reached; retry when connectivity is stable.",
            "PROVIDER_5XX": "The provider returned a temporary server error; retry later.",
            "TARGET_COOLDOWN": "The target cooldown policy blocked this publish attempt.",
            "MAX_POSTS_PER_DAY": "The target daily publishing cap was reached.",
        }
        return hints.get(self.last_error_code)
