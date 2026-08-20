"""Platforms management API routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.meta_page import MetaPage
from app.models.linkedin_account import LinkedInAccount
from app.models.meta_oauth import MetaUserToken
from app.models.linkedin_oauth import LinkedInUserToken

router = APIRouter()


class PlatformStatusResponse(BaseModel):
    platform: str
    connected: bool
    accounts_count: int


class LinkedInAccountResponse(BaseModel):
    id: int
    linkedin_id: str
    name: str
    account_type: str

    model_config = ConfigDict(from_attributes=True)


@router.get("/status", response_model=List[PlatformStatusResponse])
def get_platforms_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get connection status for all social platforms."""
    facebook_connected = db.query(MetaUserToken).filter(MetaUserToken.user_id == current_user.id).first() is not None
    facebook_pages = db.query(MetaPage).filter(MetaPage.user_id == current_user.id).count()
    
    linkedin_connected = db.query(LinkedInUserToken).filter(LinkedInUserToken.user_id == current_user.id).first() is not None
    linkedin_accounts = db.query(LinkedInAccount).filter(LinkedInAccount.user_id == current_user.id).count()
    
    return [
        PlatformStatusResponse(platform="facebook", connected=facebook_connected, accounts_count=facebook_pages),
        PlatformStatusResponse(platform="linkedin", connected=linkedin_connected, accounts_count=linkedin_accounts),
    ]


@router.get("/linkedin/accounts", response_model=List[LinkedInAccountResponse])
def list_linkedin_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List connected LinkedIn accounts."""
    return db.query(LinkedInAccount).filter(LinkedInAccount.user_id == current_user.id).all()


@router.post("/linkedin/sync")
def sync_linkedin(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Sync LinkedIn profile/accounts."""
    from app.services.linkedin_api import sync_linkedin_accounts
    try:
        count = sync_linkedin_accounts(db, current_user.id)
        return {"synced": count}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
