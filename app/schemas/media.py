"""Media schemas."""
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class MediaBase(BaseModel):
    """Base media schema."""
    filename: str
    mime_type: str
    file_size: int


class MediaResponse(MediaBase):
    """Schema for media response."""
    id: int
    user_id: int
    created_at: datetime
    # We'll provide a public URL in the response
    url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
