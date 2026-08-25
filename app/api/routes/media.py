"""Media API routes."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.media import MediaResponse, MediaProvenanceUpdate

from app.services.media_service import MediaService

router = APIRouter()


@router.post("/upload", response_model=MediaResponse, status_code=status.HTTP_201_CREATED)
async def upload_media(
    file: UploadFile = File(...),
    organization_id: Optional[int] = Query(None, description="Optional: organization ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a media file (image or video).
    """
    # Simple validation for file type
    if not file.content_type or not (file.content_type.startswith("image/") or file.content_type.startswith("video/")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image or video files are allowed"
        )
    
    service = MediaService(db)
    try:
        media = service.save_upload(file, current_user.id, organization_id)
        # Add public URL for convenience
        media_response = MediaResponse.from_orm(media)
        media_response.url = service.get_public_url(media)
        return media_response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


@router.get("/", response_model=List[MediaResponse])
def list_user_media(
    organization_id: Optional[int] = Query(None, description="Filter by Organization ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List media with optional organization filtering."""
    service = MediaService(db)
    media_list = service.list_media(current_user.id, organization_id)
    
    # Map to include URLs
    responses = []
    for m in media_list:
        res = MediaResponse.from_orm(m)
        res.url = service.get_public_url(m)
        responses.append(res)
        
    return responses


@router.patch("/{media_id}/provenance", response_model=MediaResponse)
def update_media_provenance(
    media_id: int,
    payload: MediaProvenanceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = MediaService(db)
    media = service.get_media(media_id)
    if not media:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found")
    allowed = current_user.is_admin or media.user_id == current_user.id
    if not allowed and media.organization_id:
        from app.models.organization import OrganizationMember
        allowed = bool(db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == media.organization_id,
            OrganizationMember.user_id == current_user.id,
        ).first())
    if not allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No permission to update this media")
    for field, value in payload.model_dump().items():
        setattr(media, field, value)
    db.commit()
    db.refresh(media)
    response = MediaResponse.model_validate(media)
    response.url = service.get_public_url(media)
    return response


@router.get("/{media_id}", response_model=MediaResponse)

def get_media(
    media_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get media details by ID."""
    service = MediaService(db)
    media = service.get_media(media_id)
    
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found"
        )
        
    # Permission check: owner, admin, or member of the media's organization
    has_access = False
    if current_user.is_admin or media.user_id == current_user.id:
        has_access = True
    elif media.organization_id:
        from app.models.organization import OrganizationMember
        exists = db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == media.organization_id,
            OrganizationMember.user_id == current_user.id
        ).first()
        if exists:
            has_access = True
            
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No permission to access this media"
        )
        
    res = MediaResponse.from_orm(media)
    res.url = service.get_public_url(media)
    return res
