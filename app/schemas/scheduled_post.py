"""Pydantic schemas for scheduled posts."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.models.scheduled_post import ScheduledPostStatus


class ScheduledPostCreate(BaseModel):
    """Schema for creating a scheduled post."""
    content_id: int = Field(..., description="Approved content ID")
    meta_page_id: int = Field(..., description="Page to post to")
    scheduled_at: datetime = Field(..., description="When to post (UTC)")


class ScheduledPostUpdate(BaseModel):
    """Schema for updating (e.g. cancel) a scheduled post."""
    status: Optional[ScheduledPostStatus] = None


class ScheduledPostResponse(BaseModel):
    """Schema for scheduled post response."""
    id: int
    content_id: int
    meta_page_id: int
    scheduled_at: datetime
    status: ScheduledPostStatus
    posted_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    attempt_count: int = 0
    last_error_code: Optional[str] = None
    next_retry_at: Optional[datetime] = None
    idempotency_key: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PostingPreferenceCreate(BaseModel):
    """Schema for creating/updating posting preference (safety limits)."""
    cooldown_minutes: int = Field(60, ge=1, le=1440, description="Min minutes between posts")
    max_posts_per_day: int = Field(10, ge=1, le=50, description="Max posts per day per page")


class PostingPreferenceResponse(BaseModel):
    """Schema for posting preference response."""
    id: int
    meta_page_id: int
    cooldown_minutes: int
    max_posts_per_day: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
