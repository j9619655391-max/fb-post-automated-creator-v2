from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.models.scheduled_post import ScheduledPlatform, ScheduledPostStatus


class ScheduledPostCreate(BaseModel):
    content_id: int = Field(..., description="Approved content ID")
    platform: ScheduledPlatform = Field(ScheduledPlatform.FACEBOOK, description="Publishing provider")
    meta_page_id: Optional[int] = Field(None, description="Meta Page target for Facebook or Instagram")
    linkedin_account_id: Optional[int] = Field(None, description="LinkedIn account target")
    scheduled_at: datetime = Field(..., description="When to post (UTC)")

    @model_validator(mode="after")
    def validate_target(self):
        meta_platform = self.platform in {ScheduledPlatform.FACEBOOK, ScheduledPlatform.INSTAGRAM}
        if meta_platform and not self.meta_page_id:
            raise ValueError("meta_page_id is required for Facebook or Instagram")
        if self.platform == ScheduledPlatform.LINKEDIN and not self.linkedin_account_id:
            raise ValueError("linkedin_account_id is required for LinkedIn")
        if self.platform == ScheduledPlatform.LINKEDIN and self.meta_page_id:
            raise ValueError("meta_page_id cannot be set for LinkedIn")
        if meta_platform and self.linkedin_account_id:
            raise ValueError("linkedin_account_id cannot be set for Facebook or Instagram")
        return self


class ScheduledPostUpdate(BaseModel):
    status: Optional[ScheduledPostStatus] = None


class ScheduledPostResponse(BaseModel):
    id: int
    content_id: int
    platform: ScheduledPlatform
    meta_page_id: Optional[int] = None
    linkedin_account_id: Optional[int] = None
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
    cooldown_minutes: int = Field(60, ge=1, le=1440, description="Min minutes between posts")
    max_posts_per_day: int = Field(10, ge=1, le=50, description="Max posts per day per target")


class PostingPreferenceResponse(BaseModel):
    id: int
    meta_page_id: Optional[int] = None
    linkedin_account_id: Optional[int] = None
    cooldown_minutes: int
    max_posts_per_day: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
