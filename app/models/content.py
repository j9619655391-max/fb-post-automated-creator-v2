"""Content model."""
from sqlalchemy import Boolean, Column, Integer, String, Text, Enum, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base
from app.models.scheduled_post import ScheduledPlatform


class ContentStatus(str, enum.Enum):
    """Content approval status."""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"


class Content(Base):
    """Content model for posts/articles."""
    
    __tablename__ = "content"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    body = Column(Text, nullable=False)
    status = Column(Enum(ContentStatus), default=ContentStatus.DRAFT, nullable=False, index=True)
    
    # Relationships
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    organization = relationship("Organization", backref="contents")
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    approved_at = Column(DateTime(timezone=True), nullable=True)

    # Publishing details (legacy removed; using publish_statuses relationship)
    schedule_at = Column(DateTime(timezone=True), nullable=True)
    schedule_platform = Column(Enum(ScheduledPlatform, name="scheduledplatform"), nullable=True)
    schedule_meta_page_id = Column(Integer, ForeignKey("meta_pages.id", ondelete="SET NULL"), nullable=True, index=True)
    schedule_linkedin_account_id = Column(Integer, ForeignKey("linkedin_accounts.id", ondelete="SET NULL"), nullable=True, index=True)

    # Media association
    media_id = Column(Integer, ForeignKey("media.id"), nullable=True, index=True)

    # AI generation provenance
    generated_by_ai = Column(Boolean, default=False, nullable=False, index=True)
    generation_job_id = Column(Integer, ForeignKey("content_generation_jobs.id", ondelete="SET NULL"), nullable=True, index=True)

    # Safety and feedback-learning metadata
    risk_score = Column(Integer, nullable=False, default=0, index=True)
    risk_tier = Column(String(20), nullable=False, default="low", index=True)
    risk_flags_json = Column(Text, nullable=True)

    # Relationships
    creator = relationship("User", foreign_keys=[created_by_id], backref="created_content")
    approver = relationship("User", foreign_keys=[approved_by_id], backref="approved_content")
    media = relationship("Media", foreign_keys=[media_id], backref="content_items")
    generation_job = relationship("ContentGenerationJob", foreign_keys=[generation_job_id], back_populates="content")
    publish_statuses = relationship("ContentPublishStatus", back_populates="content", cascade="all, delete-orphan")

