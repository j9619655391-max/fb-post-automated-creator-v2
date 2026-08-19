"""Pydantic schemas for content."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class ContentPublishStatusResponse(BaseModel):
    """Schema for individual target publish status (Meta, LinkedIn, etc.)."""
    meta_page_id: Optional[int] = None
    linkedin_account_id: Optional[int] = None
    status: str
    platform_post_id: Optional[str] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True

class ContentBase(BaseModel):
    """Base content schema."""
    title: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=1)

class ContentCreate(ContentBase):
    """Schema for creating content."""
    organization_id: Optional[int] = Field(None, description="Optional: organization ID for team collaboration")
    schedule_at: Optional[datetime] = Field(None, description="Optional: when to publish (UTC); used after approval")
    schedule_platform: Optional[str] = Field(None, description="Optional: facebook, instagram, or linkedin")
    schedule_meta_page_id: Optional[int] = Field(None, description="Optional: Meta page to publish to when schedule_at is set")
    schedule_linkedin_account_id: Optional[int] = Field(None, description="Optional: LinkedIn account to publish to when schedule_at is set")
    media_id: Optional[int] = Field(None, description="Optional: associated media file ID")

class ContentUpdate(BaseModel):
    """Schema for updating content."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    body: Optional[str] = Field(None, min_length=1)
    media_id: Optional[int] = Field(None, description="Optional: new media ID")
    organization_id: Optional[int] = Field(None, description="Optional: move content to another organization")

class ContentResponse(ContentBase):
    """Schema for content response."""
    id: int
    status: str
    organization_id: Optional[int]
    created_by_id: int
    approved_by_id: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    approved_at: Optional[datetime]
    schedule_at: Optional[datetime] = None
    schedule_platform: Optional[str] = None
    schedule_meta_page_id: Optional[int] = None
    schedule_linkedin_account_id: Optional[int] = None
    media_id: Optional[int] = None
    generated_by_ai: bool = False
    generation_job_id: Optional[int] = None
    publish_statuses: List[ContentPublishStatusResponse] = []

    class Config:
        from_attributes = True

class ContentApprovalRequest(BaseModel):
    """Schema for approval/rejection request."""
    approved: bool
    comment: Optional[str] = None

class PublishToFacebookRequest(BaseModel):
    """Schema for publishing content to multiple Facebook Pages."""
    meta_page_ids: List[int]

class PublishToLinkedInRequest(BaseModel):
    """Schema for publishing content to multiple LinkedIn Accounts."""
    linkedin_account_ids: List[int]

class InsightsResponse(BaseModel):
    """Schema for post insights response."""
    reach: int
    engagement: int


