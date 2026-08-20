"""Pydantic schemas for Organizations."""
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, List
from app.models.organization import OrganizationRole, SubscriptionTier


class OrgBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255, pattern="^[a-z0-9-]+$")


class OrgCreate(OrgBase):
    pass


class OrgMemberResponse(BaseModel):
    id: int
    user_id: int
    organization_id: int
    role: OrganizationRole
    joined_at: datetime
    
    # We'll include the username for display
    username: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class OrgResponse(OrgBase):
    id: int
    created_by_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Billing info
    subscription_tier: SubscriptionTier
    subscription_status: Optional[str] = None
    subscription_ends_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class OrgAddMemberRequest(BaseModel):
    user_email: str
    role: OrganizationRole = OrganizationRole.MEMBER
