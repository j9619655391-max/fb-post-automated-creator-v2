"""Pydantic schemas for Meta/Facebook pages; no token in response."""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class MetaPageResponse(BaseModel):
    """Schema for page response; token never exposed."""
    id: int
    page_id: str
    page_name: Optional[str] = None
    category: Optional[str] = None
    instagram_business_account_id: Optional[str] = None
    created_at: datetime

    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
