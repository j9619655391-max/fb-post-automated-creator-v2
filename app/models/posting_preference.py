from sqlalchemy import Column, Integer, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class PostingPreference(Base):
    """Per-target safety limits for Meta Pages and LinkedIn accounts."""

    __tablename__ = "posting_preferences"

    id = Column(Integer, primary_key=True, index=True)
    meta_page_id = Column(Integer, ForeignKey("meta_pages.id"), nullable=True, unique=True, index=True)
    linkedin_account_id = Column(Integer, ForeignKey("linkedin_accounts.id"), nullable=True, unique=True, index=True)
    cooldown_minutes = Column(Integer, default=60, nullable=False)
    max_posts_per_day = Column(Integer, default=10, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        CheckConstraint(
            "(meta_page_id IS NOT NULL AND linkedin_account_id IS NULL) OR "
            "(meta_page_id IS NULL AND linkedin_account_id IS NOT NULL)",
            name="ck_posting_preference_one_target",
        ),
    )

    meta_page = relationship("MetaPage", backref="posting_preference", uselist=False)
    linkedin_account = relationship("LinkedInAccount", backref="posting_preference", uselist=False)
