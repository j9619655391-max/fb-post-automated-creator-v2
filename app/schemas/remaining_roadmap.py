"""Schemas for social intelligence, publishing analytics, and automation controls."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class SocialSignalCreate(BaseModel):
    signal_type: str = Field(default="mention", pattern="^(mention|competitor|audience|trend)$")
    source_type: str = Field(default="manual", max_length=40)
    source_url: Optional[str] = Field(default=None, max_length=2000)
    external_id: Optional[str] = Field(default=None, max_length=1000)
    query: Optional[str] = Field(default=None, max_length=500)
    subject: Optional[str] = Field(default=None, max_length=500)
    title: str = Field(min_length=1, max_length=1000)
    excerpt: Optional[str] = Field(default=None, max_length=10000)
    publisher: Optional[str] = Field(default=None, max_length=500)
    published_at: Optional[datetime] = None
    sentiment: Optional[str] = Field(default=None, pattern="^(positive|neutral|negative|mixed)$")
    sentiment_score: Optional[float] = Field(default=None, ge=-1, le=1)
    relevance_score: float = Field(default=0, ge=0, le=1)
    engagement_count: int = Field(default=0, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SocialSignalResponse(SocialSignalCreate):
    id: int
    organization_id: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class PublishingMetricCreate(BaseModel):
    content_id: int = Field(ge=1)
    publish_status_id: Optional[int] = Field(default=None, ge=1)
    platform: str = Field(pattern="^(facebook|instagram|linkedin)$")
    platform_post_id: Optional[str] = Field(default=None, max_length=500)
    captured_at: datetime
    impressions: int = Field(default=0, ge=0)
    reach: int = Field(default=0, ge=0)
    engagements: int = Field(default=0, ge=0)
    reactions: int = Field(default=0, ge=0)
    comments: int = Field(default=0, ge=0)
    shares: int = Field(default=0, ge=0)
    clicks: int = Field(default=0, ge=0)
    video_views: int = Field(default=0, ge=0)
    saves: int = Field(default=0, ge=0)
    negative_feedback: int = Field(default=0, ge=0)
    source: str = Field(default="manual", max_length=40)
    raw: dict[str, Any] = Field(default_factory=dict)


class PublishingMetricResponse(PublishingMetricCreate):
    id: int
    organization_id: int
    engagement_rate: float
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AnalyticsSummaryResponse(BaseModel):
    organization_id: int
    metric_count: int
    totals: dict[str, int]
    by_platform: dict[str, dict[str, float | int]]
    top_content: list[dict[str, Any]]


class AutomationPolicyUpsert(BaseModel):
    approval_mode: str = Field(default="required", pattern="^(required|controlled)$")
    autopilot_enabled: bool = False
    emergency_stop: bool = False
    emergency_stop_reason: Optional[str] = Field(default=None, max_length=2000)
    max_autopilot_risk_tier: str = Field(default="low", pattern="^(low|medium|high|critical)$")
    max_autopilot_posts_per_day: int = Field(default=0, ge=0, le=1000)
    max_approval_batch_size: int = Field(default=1, ge=1, le=100)
    approval_batch_window_minutes: int = Field(default=0, ge=0, le=1440)
    max_daily_generated_drafts: int = Field(default=20, ge=1, le=10000)


class AutomationPolicyResponse(AutomationPolicyUpsert):
    id: int
    organization_id: int
    updated_by_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class BrandedMediaComposeRequest(BaseModel):
    source_media_id: int = Field(ge=1)
    theme_id: Optional[int] = Field(default=None, ge=1)
    template_family: str = Field(default="fashion-editorial", pattern="^(fashion-editorial|product-catalog|quote-card|collection-story)$")
    headline: str = Field(default="", max_length=240)
    body: str = Field(default="", max_length=3000)
    cta: str = Field(default="", max_length=300)
    website: Optional[str] = Field(default=None, max_length=500)
    handle: Optional[str] = Field(default=None, max_length=200)
    phone: Optional[str] = Field(default=None, max_length=100)
    whatsapp: Optional[str] = Field(default=None, max_length=100)
    location: Optional[str] = Field(default=None, max_length=500)


class BrandedMediaVariantResponse(BaseModel):
    id: int
    filename: str
    mime_type: str
    file_size: int
    url: str


class AutomationDecisionResponse(BaseModel):
    content_id: int
    risk_score: int
    risk_tier: str
    risk_flags: list[str]
    autopilot_allowed: bool
    reason: str
