from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.content import ContentResponse
from app.schemas.generation import GenerateDraftRequest
from app.services.content_generation_service import (
    GenerationProviderError,
    GenerationValidationError,
    generate_and_persist_draft,
)

router = APIRouter()


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
            organization_id=request.organization_id,
            idempotency_key=request.idempotency_key,
        )
    except GenerationProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except GenerationValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    content = job.content
    if content is None:
        raise HTTPException(status_code=409, detail="Generation job did not produce a draft")
    return content
