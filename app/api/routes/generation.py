from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.ai_provider_health_service import collect_ai_provider_health
from app.services.genai_client import active_provider_and_model

from app.api.dependencies import get_current_user

from app.core.database import get_db
from app.models.user import User
from app.models.media import Media
from app.schemas.content import ContentResponse
from app.schemas.generation import GenerateDraftRequest
from app.services.media_service import MediaService
from app.services.content_generation_service import (
    GenerationProviderError,
    GenerationValidationError,
    GenerationQuotaExceeded,
    generate_and_persist_draft,
)

router = APIRouter()


@router.get("/health")
def get_ai_provider_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return provider configuration and recent failure metrics without network calls."""
    return collect_ai_provider_health(db)


@router.get("/provider")
def get_ai_provider_status(current_user: User = Depends(get_current_user)):
    """Return safe AI provider readiness metadata without exposing API keys."""
    try:
        provider, model = active_provider_and_model()
    except ValueError as exc:
        return {
            "provider": "unknown",
            "model": None,
            "configured": False,
            "free_model": False,
            "fallback_enabled": settings.ai_fallback_enabled,
            "error": str(exc),
        }
    configured = bool(
        settings.gemini_api_key if provider == "gemini" else settings.openrouter_api_key
    )
    return {
        "provider": provider,
        "model": model,
        "configured": configured,
        "free_model": provider == "openrouter" and (model == "openrouter/free" or model.endswith(":free")),
        "fallback_enabled": settings.ai_fallback_enabled,
    }


@router.post("/draft", response_model=ContentResponse, status_code=status.HTTP_201_CREATED)
def generate_draft(
    request: GenerateDraftRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate one complete AI draft; approval is still required before publishing."""
    try:
        job = generate_and_persist_draft(
            db,
            current_user.id,
            category_id=request.category_id,
            category_name=request.category_name,
            extra_instruction=request.extra_instruction,
            background_preset=request.background_preset,
            organization_id=request.organization_id,
            visual_card_id=request.visual_card_id,
            idempotency_key=request.idempotency_key,
        )
    except GenerationQuotaExceeded as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except GenerationProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except GenerationValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    content = job.content
    if content is None:
        raise HTTPException(status_code=409, detail="Generation job did not produce a draft")
    if content.media_id and content.media is None:
        content.media = db.query(Media).filter(Media.id == content.media_id).first()
    if content.media:
        content.media.url = MediaService(db).get_public_url(content.media)
    return content
