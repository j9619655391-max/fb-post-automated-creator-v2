from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.scheduled_post import ScheduledPlatform, ScheduledPostStatus
from app.models.user import User
from app.schemas.scheduled_post import (
    ScheduledPostCreate,
    ScheduledPostResponse,
    PostingPreferenceCreate,
    PostingPreferenceResponse,
)
from app.services.scheduler_service import (
    cancel_scheduled_post,
    get_linkedin_posting_preference,
    get_posting_preference,
    get_scheduled_post,
    list_scheduled_posts,
    set_linkedin_posting_preference,
    set_posting_preference,
)
from app.scheduler import publish_scheduled_post_task, schedule_post

router = APIRouter()


@router.post("/", response_model=ScheduledPostResponse, status_code=status.HTTP_201_CREATED)
def schedule_post_endpoint(
    data: ScheduledPostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sp = schedule_post(
        db,
        content_id=data.content_id,
        platform=data.platform,
        scheduled_at=data.scheduled_at,
        user_id=current_user.id,
        meta_page_id=data.meta_page_id,
        linkedin_account_id=data.linkedin_account_id,
    )
    if not sp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content must be APPROVED and the selected target must belong to you",
        )
    return sp


@router.get("/", response_model=List[ScheduledPostResponse])
def list_user_scheduled_posts(
    status_filter: Optional[ScheduledPostStatus] = Query(None, alias="status"),
    platform: Optional[ScheduledPlatform] = Query(None),
    meta_page_id: Optional[int] = Query(None),
    linkedin_account_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    posts = list_scheduled_posts(
        db,
        user_id=current_user.id,
        status=status_filter,
        meta_page_id=meta_page_id,
        linkedin_account_id=linkedin_account_id,
        skip=skip,
        limit=limit,
    )
    if platform is not None:
        posts = [post for post in posts if post.platform == platform]
    return posts


@router.put("/preferences/{meta_page_id}", response_model=PostingPreferenceResponse)
def update_meta_posting_preference(
    meta_page_id: int,
    data: PostingPreferenceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    pref = set_posting_preference(db, meta_page_id, current_user.id, data.cooldown_minutes, data.max_posts_per_day)
    if pref is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meta Page not found")
    return pref


@router.get("/preferences/{meta_page_id}", response_model=PostingPreferenceResponse)
def get_meta_posting_preference(
    meta_page_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    pref = get_posting_preference(db, meta_page_id, current_user.id)
    if pref is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meta Page not found or no preference")
    return pref


@router.put("/preferences/linkedin/{linkedin_account_id}", response_model=PostingPreferenceResponse)
def update_linkedin_posting_preference(
    linkedin_account_id: int,
    data: PostingPreferenceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    pref = set_linkedin_posting_preference(
        db, linkedin_account_id, current_user.id, data.cooldown_minutes, data.max_posts_per_day
    )
    if pref is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="LinkedIn account not found")
    return pref


@router.get("/preferences/linkedin/{linkedin_account_id}", response_model=PostingPreferenceResponse)
def get_linkedin_preference(
    linkedin_account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    pref = get_linkedin_posting_preference(db, linkedin_account_id, current_user.id)
    if pref is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="LinkedIn account not found or no preference")
    return pref


@router.post("/{scheduled_post_id}/retry", response_model=ScheduledPostResponse)
def retry_scheduled_post(
    scheduled_post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Requeue a failed/dead-lettered job for immediate execution."""
    sp = get_scheduled_post(db, scheduled_post_id, current_user.id)
    if not sp or sp.status not in {ScheduledPostStatus.FAILED, ScheduledPostStatus.DEAD_LETTER}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Scheduled post is not retryable")
    sp.status = ScheduledPostStatus.PENDING
    sp.scheduled_at = datetime.now(timezone.utc)
    sp.failure_reason = None
    sp.last_error_code = None
    sp.next_retry_at = None
    sp.completed_at = None
    db.commit()
    db.refresh(sp)
    publish_scheduled_post_task.apply_async(args=[sp.id])
    return sp


@router.get("/{scheduled_post_id}", response_model=ScheduledPostResponse)
def get_scheduled_post_by_id(
    scheduled_post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sp = get_scheduled_post(db, scheduled_post_id, current_user.id)
    if not sp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scheduled post not found")
    return sp


@router.patch("/{scheduled_post_id}/cancel")
def cancel_post(
    scheduled_post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not cancel_scheduled_post(db, scheduled_post_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Scheduled post not found or not cancellable")
    return {"cancelled": True}
