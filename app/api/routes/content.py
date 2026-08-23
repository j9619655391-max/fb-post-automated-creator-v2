"""Content API routes."""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.media import Media
from app.models.content_package import ContentPackage
from app.models.user import User
from app.models.content import ContentStatus
from app.schemas.content import (
    ContentCreate,
    ContentUpdate,
    ContentResponse,
    ContentApprovalRequest,
    PublishToFacebookRequest,
    PublishToLinkedInRequest,
        InsightsResponse,
)
from app.schemas.content_package import ContentPackageCreate, ContentPackageResponse
from app.services.content_package_service import create_content_packages, content_package_payload

from app.services.content_service import ContentService
from app.services.fb_api import publish_to_facebook
from app.services.linkedin_api import publish_to_linkedin

router = APIRouter()


def _hydrate_media(content, db: Session):
    if content.media_id and content.media is None:
        content.media = db.query(Media).filter(Media.id == content.media_id).first()
    if content.media:
        from app.services.media_service import MediaService
        content.media.url = MediaService(db).get_public_url(content.media)
    return content


def _package_response(package: ContentPackage, db: Session) -> dict:
    data = content_package_payload(package)
    media_rows = db.query(Media).filter(Media.id.in_(data["media_variant_ids"])).all() if data["media_variant_ids"] else []
    by_id = {media.id: media for media in media_rows}
    from app.services.media_service import MediaService
    media_service = MediaService(db)
    data["media_variant_urls"] = [media_service.get_public_url(by_id[media_id]) for media_id in data["media_variant_ids"] if media_id in by_id]
    return data


@router.post("/", response_model=ContentResponse, status_code=status.HTTP_201_CREATED)
def create_content(
    content_data: ContentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new content draft."""
    service = ContentService(db)
    try:
        content = service.create_content(content_data, current_user.id)
        return _hydrate_media(content, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=List[ContentResponse])
def list_content(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[str] = Query(None, alias="status"),
    organization_id: Optional[int] = Query(None, description="Filter by Organization ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List content with optional filters."""
    service = ContentService(db)
    
    content_status = None
    if status_filter:
        try:
            # Accept enum value (e.g. "approved") or name (e.g. "APPROVED")
            try:
                content_status = ContentStatus(status_filter)
            except ValueError:
                content_status = ContentStatus[status_filter.upper()]
        except (ValueError, KeyError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_filter}"
            )
    
    # Non-admins see only their own content (if personal) or org content
    filter_user_id = None if current_user.is_admin else current_user.id
    content_list = service.list_content(
        skip=skip,
        limit=limit,
        status=content_status,
        user_id=filter_user_id,
        organization_id=organization_id,
    )

    # Populate media URLs
    return [_hydrate_media(content, db) for content in content_list]


@router.get("/{content_id}", response_model=ContentResponse)
def get_content(
    content_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get content by ID."""
    service = ContentService(db)
    content = service.get_content(content_id)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    return _hydrate_media(content, db)


@router.patch("/{content_id}", response_model=ContentResponse)
def update_content(
    content_id: int,
    content_data: ContentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update content (only draft content)."""
    service = ContentService(db)
    try:
        content = service.update_content(content_id, content_data, current_user.id)
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found"
            )
        return content
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{content_id}/packages", response_model=List[ContentPackageResponse])
def create_content_package_variants(
    content_id: int,
    payload: ContentPackageCreate,
    organization_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        from app.models.organization import OrganizationMember
        if not db.query(OrganizationMember).filter(OrganizationMember.organization_id == organization_id, OrganizationMember.user_id == current_user.id).first():
            raise ValueError("Not a member of this workspace")
        packages = create_content_packages(db, content_id, organization_id, payload.platforms, payload.theme_id, payload.opportunity_id)
        return [_package_response(package, db) for package in packages]
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{content_id}/packages", response_model=List[ContentPackageResponse])
def list_content_package_variants(
    content_id: int,
    organization_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.organization import OrganizationMember
    if not db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == organization_id,
        OrganizationMember.user_id == current_user.id,
    ).first():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this workspace")
    packages = db.query(ContentPackage).filter(
        ContentPackage.source_content_id == content_id,
        ContentPackage.organization_id == organization_id,
    ).order_by(ContentPackage.platform).all()
    return [_package_response(package, db) for package in packages]


@router.post("/{content_id}/submit", response_model=ContentResponse)

def submit_for_approval(
    content_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit content for approval."""
    service = ContentService(db)
    try:
        content = service.submit_for_approval(content_id, current_user.id)
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found"
            )
        return content
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{content_id}/approve", response_model=ContentResponse)
def approve_content(
    content_id: int,
    approval_data: ContentApprovalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Approve or reject content (requires admin)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can approve/reject content"
        )
    
    service = ContentService(db)
    try:
        content = service.approve_content(content_id, approval_data, current_user.id)
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found"
            )
        return content
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{content_id}/publish-to-facebook", response_model=ContentResponse)
def publish_content_to_facebook(
    content_id: int,
    body: PublishToFacebookRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Publish content to multiple Facebook Pages. Updates content publish_statuses."""
    try:
        content = publish_to_facebook(db, content_id, body.meta_page_ids, current_user.id)
        return content
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

@router.post("/{content_id}/publish-to-linkedin", response_model=ContentResponse)
def publish_content_to_linkedin(
    content_id: int,
    body: PublishToLinkedInRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Publish content to multiple LinkedIn Accounts (Profiles/Pages)."""
    try:
        content = publish_to_linkedin(db, content_id, body.linkedin_account_ids, current_user.id)
        return content
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_content(
    content_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete content (only draft content)."""
    service = ContentService(db)
    try:
        success = service.delete_content(content_id, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{content_id}/insights", response_model=InsightsResponse)
def get_content_insights(
    content_id: int,
    meta_page_id: int = Query(..., description="The ID of the MetaPage to get insights for"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch insights for a published post on a specific Meta Page."""
    service = ContentService(db)
    content = service.get_content(content_id)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    from app.models.content_execution import ContentPublishStatus, PublishStatusEnum
    publish_status = db.query(ContentPublishStatus).filter(
        ContentPublishStatus.content_id == content_id,
        ContentPublishStatus.meta_page_id == meta_page_id,
        ContentPublishStatus.status == PublishStatusEnum.POSTED
    ).first()
    
    if not publish_status or not publish_status.platform_post_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content has not been posted to this Facebook page yet"
        )
    
    from app.services.facebook_pages_service import get_post_insights
    try:
        insights = get_post_insights(db, publish_status.platform_post_id, meta_page_id, current_user.id)
        return insights
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

