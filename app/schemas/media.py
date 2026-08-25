"""Media schemas."""
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from pydantic import Field


class MediaProvenanceUpdate(BaseModel):
    source_kind: str = Field(pattern="^(uploaded|workspace_media|stock_licensed|ai_generated|deterministic_text_card)$")
    source_url: Optional[str] = Field(default=None, max_length=2048)
    license_info: Optional[str] = Field(default=None, max_length=5000)
    attribution: Optional[str] = Field(default=None, max_length=2000)
    provenance_status: str = Field(default="pending", pattern="^(unverified|pending|verified|rejected)$")


class MediaBase(BaseModel):

    """Base media schema."""
    filename: str
    mime_type: str
    file_size: int
    source_kind: str = "uploaded"
    source_url: Optional[str] = None
    license_info: Optional[str] = None
    attribution: Optional[str] = None
    provenance_status: str = "unverified"


class MediaResponse(MediaBase):
    """Schema for media response."""
    id: int
    user_id: int
    created_at: datetime
    # We'll provide a public URL in the response
    url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
