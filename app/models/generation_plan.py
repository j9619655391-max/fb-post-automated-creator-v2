import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class GenerationPlanStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"


class GenerationRecurrence(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"


class ApprovalMode(str, enum.Enum):
    REQUIRED = "required"
    CONTROLLED = "controlled"


class ContentGenerationPlan(Base):
    """Recurring plan that creates approval-required AI drafts."""

    __tablename__ = "content_generation_plans"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    category_id = Column(Integer, ForeignKey("content_categories.id", ondelete="SET NULL"), nullable=True)
    category_name = Column(String(200), nullable=True)
    extra_instruction = Column(Text, nullable=True)
    recurrence = Column(Enum(GenerationRecurrence), nullable=False, default=GenerationRecurrence.DAILY)
    approval_mode = Column(Enum(ApprovalMode), nullable=False, default=ApprovalMode.REQUIRED)
    status = Column(Enum(GenerationPlanStatus), nullable=False, default=GenerationPlanStatus.ACTIVE, index=True)
    next_run_at = Column(DateTime(timezone=True), nullable=False, index=True)
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    last_provider = Column(String(100), nullable=True)
    last_error_code = Column(String(100), nullable=True)
    last_error_message = Column(Text, nullable=True)
    failure_count = Column(Integer, nullable=False, default=0)
    last_retry_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    organization = relationship("Organization")
    creator = relationship("User")
    category = relationship("ContentCategory")
