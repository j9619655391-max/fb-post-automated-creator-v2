import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class GenerationStatus(str, enum.Enum):
    PENDING = "pending"
    GENERATING = "generating"
    SUCCEEDED = "succeeded"
    VALIDATION_FAILED = "validation_failed"
    FAILED = "failed"


class ContentGenerationJob(Base):
    """Auditable record of an AI generation request and its persisted draft result."""

    __tablename__ = "content_generation_jobs"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True)
    requested_by_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("content_categories.id", ondelete="SET NULL"), nullable=True, index=True)
    category_name = Column(String(200), nullable=True)
    extra_instruction = Column(Text, nullable=True)
    model = Column(String(100), nullable=True)
    provider = Column(String(50), nullable=True)
    status = Column(Enum(GenerationStatus), default=GenerationStatus.PENDING, nullable=False, index=True)
    idempotency_key = Column(String(128), nullable=True, unique=True, index=True)
    title = Column(String(200), nullable=True)
    body = Column(Text, nullable=True)
    hook = Column(String(500), nullable=True)
    call_to_action = Column(String(500), nullable=True)
    hashtags_json = Column(Text, nullable=True)
    risk_flags_json = Column(Text, nullable=True)
    error_code = Column(String(100), nullable=True)
    error_message = Column(String(1000), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    content = relationship("Content", back_populates="generation_job", uselist=False)
    organization = relationship("Organization")
    requested_by = relationship("User")
    category = relationship("ContentCategory")
