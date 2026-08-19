from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class ContentGenerationUsage(Base):
    """Token and cost accounting for one AI generation request."""

    __tablename__ = "content_generation_usage"

    id = Column(Integer, primary_key=True, index=True)
    generation_job_id = Column(Integer, ForeignKey("content_generation_jobs.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True)
    requested_by_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    provider = Column(String(50), nullable=False)
    model = Column(String(100), nullable=False)
    prompt_token_count = Column(Integer, nullable=False, default=0)
    candidates_token_count = Column(Integer, nullable=False, default=0)
    thoughts_token_count = Column(Integer, nullable=False, default=0)
    cached_content_token_count = Column(Integer, nullable=False, default=0)
    total_token_count = Column(Integer, nullable=False, default=0)
    input_cost_per_million_usd = Column(Numeric(12, 6), nullable=False, default=0)
    output_cost_per_million_usd = Column(Numeric(12, 6), nullable=False, default=0)
    cost_usd = Column(Numeric(14, 8), nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    generation_job = relationship("ContentGenerationJob", backref="usage")
    organization = relationship("Organization")
    requested_by = relationship("User")
