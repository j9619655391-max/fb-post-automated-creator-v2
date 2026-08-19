"""Viral Content Engine API: category rotation, hook templates, AI theme generation. All advisory; user decides."""
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.vce import (
    ContentCategoryResponse,
    HookTemplateResponse,
    SuggestedCategoryResponse,
    SuggestedTemplateResponse,
    GenerateThemesResponse,
)
from app.services.vce_service import (
    list_categories,
    get_rotated_category_for_today,
    list_templates,
    get_suggested_template_for_today,
    get_share_psychology_tips,
)
from app.services.theme_generation_service import (
    generate_themes,
    is_theme_generation_available,
)

router = APIRouter()


@router.get("/categories", response_model=List[ContentCategoryResponse])
def get_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all content categories (for rotation and variety). Advisory only."""
    return list_categories(db)


@router.get("/categories/today", response_model=SuggestedCategoryResponse)
def get_todays_category(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get today's suggested category (rotation). Advisory only; user decides what to post."""
    category = get_rotated_category_for_today(db)
    if not category:
        raise HTTPException(status_code=404, detail="No categories defined; add categories first.")
    return SuggestedCategoryResponse(category=ContentCategoryResponse.model_validate(category))


@router.get("/templates", response_model=List[HookTemplateResponse])
def get_templates(
    category_id: Optional[int] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List hook-based templates (placeholders: {hook}, {body}, {cta}). Advisory only."""
    return list_templates(db, category_id=category_id)


@router.get("/suggested-template", response_model=SuggestedTemplateResponse)
def get_suggested_template(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get suggested template for today (by category rotation). Advisory only."""
    template = get_suggested_template_for_today(db)
    if not template:
        raise HTTPException(status_code=404, detail="No templates defined; add templates first.")
    category = None
    if template.category_id and template.category:
        category = ContentCategoryResponse.model_validate(template.category)
    return SuggestedTemplateResponse(
        template=HookTemplateResponse.model_validate(template),
        suggested_category=category,
    )


@router.get("/share-psychology-tips")
def share_psychology_tips(
    current_user: User = Depends(get_current_user),
):
    """Get advisory share-psychology tips (emotion, utility, clarity, timing, CTA). All advisory; user decides."""
    return {"advisory_only": True, "tips": get_share_psychology_tips()}


@router.get("/generate-themes", response_model=GenerateThemesResponse)
def get_generated_themes(
    category_id: Optional[int] = Query(None, description="Filter themes by category ID"),
    category_name: Optional[str] = Query(None, description="Category name for context (e.g. Motivation)"),
    count: int = Query(5, ge=1, le=15, description="Number of themes to generate"),
    extra_instruction: Optional[str] = Query(None, description="Optional extra context for the AI"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate content themes using Gemini API. Requires GEMINI_API_KEY. Advisory only."""
    available = is_theme_generation_available()
    if not available:
        return GenerateThemesResponse(themes=[], available=False)
    themes = generate_themes(
        db,
        category_id=category_id,
        category_name=category_name,
        count=count,
        extra_instruction=extra_instruction,
        user_id=current_user.id,
    )
    return GenerateThemesResponse(themes=themes, available=True)
