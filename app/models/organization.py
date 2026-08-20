"""Organization and OrganizationMember models for team collaboration."""
import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class OrganizationRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    EDITOR = "editor"


class SubscriptionTier(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    AGENCY = "agency"


class Organization(Base):
    """Organization/Workspace model."""
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Billing fields
    stripe_customer_id = Column(String(255), nullable=True, unique=True)
    subscription_tier = Column(Enum(SubscriptionTier), default=SubscriptionTier.FREE, nullable=False)
    subscription_status = Column(String(50), default="active", nullable=True)  # active, past_due, canceled, etc.
    subscription_ends_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    members = relationship("OrganizationMember", back_populates="organization", cascade="all, delete-orphan")
    workspace_profile = relationship(
        "WorkspaceProfile",
        back_populates="organization",
        uselist=False,
        cascade="all, delete-orphan",
    )
    workspace_sources = relationship(
        "WorkspaceSource",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    created_by = relationship("User", backref="created_organizations")


class OrganizationMember(Base):
    """Mapping between Users and Organizations with roles."""
    __tablename__ = "organization_members"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(Enum(OrganizationRole), default=OrganizationRole.MEMBER, nullable=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    organization = relationship("Organization", back_populates="members")
    user = relationship("User", backref="organization_memberships")

    __table_args__ = (UniqueConstraint("organization_id", "user_id", name="uq_org_user"),)
