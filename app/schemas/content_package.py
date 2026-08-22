from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ContentPackageCreate(BaseModel):
    platforms: list[str] = Field(default_factory=lambda: ["facebook", "instagram", "linkedin"], min_length=1, max_length=3)
    theme_id: Optional[int] = Field(default=None, ge=1)
    opportunity_id: Optional[int] = Field(default=None, ge=1)


class ContentPackageResponse(BaseModel):
    id: int
    organization_id: Optional[int] = None
    source_content_id: int
    theme_id: Optional[int] = None
    opportunity_id: Optional[int] = None
    platform: str
    headline: Optional[str] = None
    caption: str
    cta: Optional[str] = None
    hashtags: list[str]
    source_urls: list[str]
    media_variant_ids: list[int]
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
