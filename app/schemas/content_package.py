from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class ContentPackageCreate(BaseModel):
    platforms: list[str] = Field(default_factory=lambda: ["facebook", "instagram", "linkedin"], min_length=1, max_length=3)
    theme_id: Optional[int] = Field(default=None, ge=1)
    opportunity_id: Optional[int] = Field(default=None, ge=1)
    image_text: Optional[str] = Field(default=None, max_length=160)
    alt_text: Optional[str] = Field(default=None, max_length=500)
    objective: Optional[str] = Field(default=None, max_length=120)
    creative_archetype: Optional[str] = Field(default=None, max_length=120)
    source_refs: list[str] = Field(default_factory=list, max_length=40)
    claim_refs: list[str] = Field(default_factory=list, max_length=40)
    source_ref_ids: list[int] = Field(default_factory=list, max_length=40)
    claim_ref_ids: list[int] = Field(default_factory=list, max_length=40)
    visual_brief: dict[str, Any] = Field(default_factory=dict)
    asset_provenance: dict[str, Any] = Field(default_factory=dict)
    media_variant_ids_by_platform: dict[str, list[int]] = Field(default_factory=dict)


class ContentPackageResponse(BaseModel):
    id: int
    organization_id: Optional[int] = None
    source_content_id: int
    theme_id: Optional[int] = None
    opportunity_id: Optional[int] = None
    platform: str
    headline: Optional[str] = None
    image_text: Optional[str] = None
    caption: str
    alt_text: Optional[str] = None
    cta: Optional[str] = None
    objective: Optional[str] = None
    creative_archetype: Optional[str] = None
    hashtags: list[str]
    tags: list[str]
    source_urls: list[str]
    source_refs: list[str] = []
    claim_refs: list[str] = []
    source_ref_ids: list[int] = []
    claim_ref_ids: list[int] = []
    evidence_status: str = "unverified"
    visual_brief: dict = {}
    asset_provenance: dict = {}
    media_variant_ids: list[int]
    visual_qa_status: str = "not_run"
    visual_qa_flags: list[str] = []
    media_variant_urls: list[str] = []
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
