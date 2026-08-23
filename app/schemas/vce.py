"""Pydantic schemas for Viral Content Engine (advisory)."""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ContentCategoryResponse(BaseModel):
    """Content category for rotation suggestions."""
    id: int
    name: str
    slug: str
    sort_order: int
    created_at: datetime

    model_config = {"from_attributes": True}


class HookTemplateResponse(BaseModel):
    """Hook-based template with placeholders."""
    id: int
    name: str
    body_template: str
    default_hook: Optional[str] = None
    default_cta: Optional[str] = None
    category_id: Optional[int] = None
    sort_order: int
    created_at: datetime

    model_config = {"from_attributes": True}


class SuggestedCategoryResponse(BaseModel):
    """Workspace-aware category recommendation; advisory only."""
    category: ContentCategoryResponse
    reason: Optional[str] = None
    evidence_terms: list[str] = []
    advisory_only: bool = True


class SuggestedTemplateResponse(BaseModel):
    """Suggested template for today/category; advisory only."""
    template: HookTemplateResponse
    suggested_category: Optional[ContentCategoryResponse] = None
    advisory_only: bool = True


class GenerateThemesResponse(BaseModel):
    """AI-generated content themes (Gemini). Advisory only."""
    themes: list[str]
    available: bool = True  # False if Gemini API key not configured
