"""Schemas for workspace business intelligence and source provenance."""
from datetime import datetime
from typing import Any, Optional

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field


class WorkspaceProfileUpsert(BaseModel):
    business_description: Optional[str] = Field(default=None, max_length=10000)
    mission: Optional[str] = Field(default=None, max_length=5000)
    tagline: Optional[str] = Field(default=None, max_length=500)
    industry: Optional[str] = Field(default=None, max_length=255)
    services: list[str] = Field(default_factory=list, max_length=100)
    products: list[str] = Field(default_factory=list, max_length=100)
    target_audience: Optional[str] = Field(default=None, max_length=5000)
    locations: list[str] = Field(default_factory=list, max_length=100)
    brand_voice: Optional[str] = Field(default=None, max_length=5000)
    tone: Optional[str] = Field(default=None, max_length=100)
    visual_style: Optional[str] = Field(default=None, max_length=5000)
    brand_colors: list[str] = Field(default_factory=list, max_length=20)
    font_preferences: list[str] = Field(default_factory=list, max_length=20)
    preferred_content_formats: list[str] = Field(default_factory=list, max_length=20)
    content_cadence: dict[str, Any] = Field(default_factory=dict)
    keywords: list[str] = Field(default_factory=list, max_length=100)
    watch_terms: list[str] = Field(default_factory=list, max_length=100)
    competitor_urls: list[AnyHttpUrl] = Field(default_factory=list, max_length=50)
    preferred_languages: list[str] = Field(default_factory=list, max_length=20)
    contact_email: Optional[str] = Field(default=None, max_length=320)
    contact_phone: Optional[str] = Field(default=None, max_length=80)
    whatsapp_display_phone: Optional[str] = Field(default=None, max_length=80)
    whatsapp_business_account_id: Optional[str] = Field(default=None, max_length=255)
    website_url: Optional[AnyHttpUrl] = None
    linkedin_url: Optional[AnyHttpUrl] = None
    facebook_url: Optional[AnyHttpUrl] = None
    instagram_url: Optional[AnyHttpUrl] = None
    whatsapp_url: Optional[AnyHttpUrl] = None
    logo_media_id: Optional[int] = Field(default=None, ge=1)
    telegram_approval_chat_id: Optional[str] = Field(default=None, max_length=255)
    telegram_approval_user_id: Optional[str] = Field(default=None, max_length=255)
    telegram_approval_enabled: bool = False
    approval_required: bool = True
    approved_claims: list[str] = Field(default_factory=list, max_length=100)
    prohibited_claims: list[str] = Field(default_factory=list, max_length=100)


class WorkspaceProfileResponse(WorkspaceProfileUpsert):
    id: int
    organization_id: int
    last_refreshed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class WorkspaceSourceCreate(BaseModel):
    source_type: str = Field(pattern="^(website|facebook_page|instagram_account|linkedin_page|whatsapp_business|rss|news|research|manual)$")
    provider: Optional[str] = Field(default=None, max_length=50)
    url: Optional[AnyHttpUrl] = None
    external_id: Optional[str] = Field(default=None, max_length=255)
    title: Optional[str] = Field(default=None, max_length=500)
    content_text: Optional[str] = Field(default=None, max_length=200000)
    excerpt: Optional[str] = Field(default=None, max_length=10000)
    metadata: dict[str, Any] = Field(default_factory=dict)
    trust_level: str = Field(default="user_supplied", pattern="^(user_supplied|official_api|public_metadata|manual_reviewed)$")
    review_status: str = Field(default="pending", pattern="^(pending|approved|rejected)$")


class WorkspaceSourceReview(BaseModel):
    review_status: str = Field(pattern="^(pending|approved|rejected)$")
    review_note: Optional[str] = Field(default=None, max_length=2000)


class WorkspaceSourceResponse(WorkspaceSourceCreate):
    id: int
    organization_id: int
    is_active: bool
    last_fetched_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ContentOpportunityResponse(BaseModel):
    id: int
    organization_id: int
    source_type: str
    source_url: Optional[str] = None
    publisher: Optional[str] = None
    external_id: Optional[str] = None
    title: str
    summary: Optional[str] = None
    source_published_at: Optional[datetime] = None
    discovered_at: datetime
    freshness_score: float
    relevance_score: float
    trust_score: float
    status: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkspaceIntelligenceResponse(BaseModel):
    profile: Optional[WorkspaceProfileResponse] = None
    sources: list[WorkspaceSourceResponse] = Field(default_factory=list)
    source_count: int
    approved_source_count: int
