"""Scheduled post: user schedules content to be published to a page at a given time."""
import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class ScheduledPostStatus(str, enum.Enum):
    """Status of a scheduled post."""
    PENDING = "pending"       # Scheduled (waiting for publish time)
    PROCESSING = "processing" # Celery task is running
    POSTED = "posted"
    CANCELLED = "cancelled"
    FAILED = "failed"
    RETRYING = "retrying"
    PARTIALLY_FAILED = "partially_failed"
    DEAD_LETTER = "dead_letter"


class ScheduledPost(Base):
    """User-scheduled post: approved content + page + scheduled time. Scheduler executes only these."""
    __tablename__ = "scheduled_posts"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("content.id"), nullable=False, index=True)
    meta_page_id = Column(Integer, ForeignKey("meta_pages.id"), nullable=False, index=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=False, index=True)
    status = Column(Enum(ScheduledPostStatus), default=ScheduledPostStatus.PENDING, nullable=False, index=True)
    posted_at = Column(DateTime(timezone=True), nullable=True)
    failure_reason = Column(String(512), nullable=True)  # If status=FAILED
    attempt_count = Column(Integer, nullable=False, default=0)
    last_error_code = Column(String(100), nullable=True)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    idempotency_key = Column(String(255), nullable=True, unique=True, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    content = relationship("Content", backref="scheduled_posts")
    meta_page = relationship("MetaPage", backref="scheduled_posts")
