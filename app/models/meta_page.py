"""Meta/Facebook Page model; page access token stored encrypted at rest."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class MetaPage(Base):
    """Facebook Page linked to a user; page access token encrypted at rest."""
    __tablename__ = "meta_pages"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    page_id = Column(String(64), nullable=False, index=True)  # Meta Page ID
    page_name = Column(String(255), nullable=True)
    category = Column(String(128), nullable=True)
    instagram_business_account_id = Column(String(64), nullable=True, index=True)
    access_token_encrypted = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (UniqueConstraint("user_id", "page_id", name="uq_meta_pages_user_page"),)

    user = relationship("User", backref="meta_pages")
