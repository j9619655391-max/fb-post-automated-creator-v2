from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class BrandThemeUpsert(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    slug: str = Field(min_length=1, max_length=120, pattern=r"^[a-z0-9][a-z0-9-]*$")
    description: Optional[str] = Field(default=None, max_length=2000)
    visual_style: Optional[str] = Field(default=None, max_length=5000)
    color_palette: list[str] = Field(default_factory=list, max_length=20)
    typography: dict[str, Any] = Field(default_factory=dict)
    logo_position: str = Field(default="bottom_right", pattern="^(top_left|top_right|bottom_left|bottom_right|center)$")
    background_style: Optional[str] = Field(default=None, max_length=255)
    supported_formats: list[str] = Field(default_factory=list, max_length=20)
    is_active: bool = True
    is_default: bool = False


class BrandThemeResponse(BrandThemeUpsert):
    id: int
    organization_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
