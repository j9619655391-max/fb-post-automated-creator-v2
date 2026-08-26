"""Schemas for social intelligence, publishing analytics, and automation controls."""

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field


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
    template_family: str = Field(default="service-editorial", pattern="^(fashion-editorial|service-editorial|product-catalog|technology-explainer|quote-card|collection-story)$")
    background_preset: str = Field(default="midnight-aurora", pattern="^(midnight-aurora|warm-paper|rose-editorial|sunset-glow|minimal-ink|neon-night)$")
    headline: str = Field(default="", max_length=240)
    image_text: Optional[str] = Field(default=None, max_length=160)
    body: str = Field(default="", max_length=3000)
    alt_text: Optional[str] = Field(default=None, max_length=500)
    cta: str = Field(default="", max_length=300)
    objective: Optional[str] = Field(default=None, max_length=120)
    creative_archetype: Optional[str] = Field(default=None, max_length=120)
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


class CompleteSocialPostComposeRequest(BrandedMediaComposeRequest):
    # A quote-card may intentionally use a deterministic branded text background.
    # Other template families still require source_media_id at route validation.
    source_media_id: Optional[int] = Field(default=None, ge=1)
    use_branded_text_card: bool = False
    platforms: list[Literal["facebook", "instagram", "linkedin"]] = Field(
        default_factory=lambda: ["facebook", "instagram", "linkedin"],
        min_length=1,
        max_length=3,
    )
    caption: Optional[str] = Field(default=None, max_length=5000)
    hashtags: list[str] = Field(default_factory=list, max_length=40)
    tags: list[str] = Field(default_factory=list, max_length=40)
    source_refs: list[str] = Field(default_factory=list, max_length=40)
    claim_refs: list[str] = Field(default_factory=list, max_length=40)
    source_ref_ids: list[int] = Field(default_factory=list, max_length=40)
    claim_ref_ids: list[int] = Field(default_factory=list, max_length=40)
    visual_brief: dict[str, Any] = Field(default_factory=dict)
    asset_provenance: dict[str, Any] = Field(default_factory=dict)


class CompleteSocialPostPackageResponse(BaseModel):
    content_id: int
    package_id: int
    platform: Literal["facebook", "instagram", "linkedin"]
    image: BrandedMediaVariantResponse
    headline: str
    image_text: Optional[str] = None
    caption: str
    alt_text: Optional[str] = None
    cta: Optional[str] = None
    objective: Optional[str] = None
    creative_archetype: Optional[str] = None
    hashtags: list[str]
    tags: list[str]
    source_refs: list[str] = []
    claim_refs: list[str] = []
    source_ref_ids: list[int] = []
    claim_ref_ids: list[int] = []
    evidence_status: str = "unverified"
    visual_brief: dict[str, Any] = {}
    asset_provenance: dict[str, Any] = {}
    visual_qa_status: str = "not_run"
    visual_qa_flags: list[str] = []
    status: str


class PamphletBriefCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    objective: Optional[str] = Field(default=None, max_length=120)
    audience: Optional[str] = Field(default=None, max_length=500)
    panel_count: int = Field(default=2, ge=2, le=6)
    paper_size: str = Field(default="A4", pattern="^(A4|A5|letter|custom)$")
    orientation: str = Field(default="landscape", pattern="^(landscape|portrait)$")
    fold_style: str = Field(default="half-fold", pattern="^(none|half-fold|tri-fold|z-fold|gate-fold)$")
    trim_width_mm: int = Field(default=297, ge=50, le=1000)
    trim_height_mm: int = Field(default=210, ge=50, le=1000)
    bleed_mm: int = Field(default=3, ge=0, le=20)
    safe_area_mm: int = Field(default=5, ge=1, le=50)
    qr_url: Optional[AnyHttpUrl] = None
    accessibility_text: Optional[str] = Field(default=None, max_length=5000)
    content: dict[str, Any] = Field(default_factory=dict)
    approval_required: bool = True


class PamphletBriefResponse(PamphletBriefCreate):
    id: int
    organization_id: int
    status: str
    created_by_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class AutomationDecisionResponse(BaseModel):
    content_id: int
    risk_score: int
    risk_tier: str
    risk_flags: list[str]
    autopilot_allowed: bool
    reason: str
